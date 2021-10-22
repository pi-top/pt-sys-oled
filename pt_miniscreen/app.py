import logging
from threading import Event, Thread

from pitop import Pitop

from .bootsplash import Bootsplash
from .event import AppEvents, post_event, subscribe
from .menu_manager import MenuManager
from .screensaver import StarfieldScreensaver
from .sleep_manager import SleepManager
from .state import DisplayState, DisplayStateManager

logger = logging.getLogger(__name__)


class App:
    TIMEOUTS = {
        DisplayState.DIM: 20,
        DisplayState.SCREENSAVER: 60,
        DisplayState.WAKING: 0.6,
        DisplayState.RUNNING_ACTION: 30,
    }

    def __init__(self):
        logger.debug("Initialising app...")

        self.__thread = Thread(target=self._main, args=())
        self.__stop = False

        self.last_shown_image = None

        self.user_gave_back_control_event = Event()

        self.miniscreen = Pitop().miniscreen

        self.miniscreen.when_user_controlled = lambda: self.set_is_user_controlled(True)
        self.miniscreen.when_system_controlled = lambda: self.set_is_user_controlled(
            False
        )

        self.splash = Bootsplash(self.miniscreen)

        self.menu_manager = MenuManager(
            self.miniscreen.size,
            self.miniscreen.mode,
        )

        self.screensaver = StarfieldScreensaver(
            self.miniscreen.mode, self.miniscreen.size
        )
        self.state_manager = DisplayStateManager()

        def callback_handler(callback):
            if self.state_manager.state != DisplayState.WAKING:
                self.state_manager.user_activity_timer.reset()

            if self.state_manager.state == DisplayState.ACTIVE:
                if callable(callback):
                    logger.debug("callback_handler - Executing callback")
                    callback()
                return

            self.sleep_manager.wake()

        self.miniscreen.up_button.when_released = lambda: post_event(
            AppEvents.UP_BUTTON_PRESS, callback_handler
        )
        self.miniscreen.down_button.when_released = lambda: post_event(
            AppEvents.DOWN_BUTTON_PRESS, callback_handler
        )
        self.miniscreen.select_button.when_released = lambda: post_event(
            AppEvents.SELECT_BUTTON_PRESS, callback_handler
        )
        self.miniscreen.cancel_button.when_released = lambda: post_event(
            AppEvents.CANCEL_BUTTON_PRESS, callback_handler
        )

        subscribe(AppEvents.BUTTON_ACTION_START, self.start_current_menu_action)
        self.sleep_manager = SleepManager(self.state_manager, self.miniscreen)

    def start(self):
        self.__thread = Thread(target=self._main, args=())
        self.__thread.daemon = True
        self.__thread.start()

    def stop(self):
        self.__stop = True
        if self.__thread and self.__thread.is_alive():
            self.__thread.join()
        logger.info("Stopped miniscreen app")

    def handle_startup_animation(self):
        if not self.splash.has_played():
            logger.info("Not played boot animation this session - starting...")
            self.splash.play()
            logger.info("Finished startup animation")

    @property
    def user_has_control(self):
        return self.miniscreen.is_active

    def handle_action(self):
        logger.debug("Resetting activity timer to prevent dimming...")
        self.state_manager.user_activity_timer.reset()

        time_since_action_started = self.state_manager.action_timer.elapsed_time

        logger.debug(f"Time since action started: {time_since_action_started}")

        if self.menu_manager.current_menu.current_page.action_process.is_alive():
            logger.debug("Action not yet completed")
            return

        if time_since_action_started > self.TIMEOUTS[DisplayState.RUNNING_ACTION]:
            logger.info("Action timed out - setting state to WAKING")
            self.state_manager.state = DisplayState.WAKING

            logger.info("Notifying renderer to display 'unknown' action state")
            self.menu_manager.current_menu.current_page.set_unknown_state()
            return

        logger.info("Action completed - setting state to WAKING")
        self.state_manager.state = DisplayState.WAKING
        logger.info("Resetting state of hotspot to re-renderer current state")

        self.menu_manager.current_menu.current_page.hotspot.reset()

    @property
    def time_since_last_active(self):
        return self.state_manager.user_activity_timer.elapsed_time

    def handle_active_time(self):
        logger.debug("Checking for state change based on inactive time...")

        if self.state_manager.state == DisplayState.WAKING:
            if self.time_since_last_active < self.TIMEOUTS[DisplayState.WAKING]:
                return

            self.state_manager.state = DisplayState.ACTIVE

        if self.time_since_last_active < self.TIMEOUTS[DisplayState.DIM]:
            return

        if self.state_manager.state == DisplayState.ACTIVE:
            logger.info("Going to sleep...")
            self.sleep_manager.sleep()
            return

    def display_current_menu_image(self):
        logger.debug("Updating scroll position...")
        self.menu_manager.update_current_menu_scroll_position()

        logger.debug("Displaying current menu's image...")
        self.display(self.menu_manager.current_menu.image)

        logger.debug("Waiting until timeout or until page has changed...")
        self.menu_manager.wait_until_timeout_or_should_redraw()
        logger.debug("Done waiting!")

    def _main(self):
        self.handle_startup_animation()

        logger.info("Starting main loop...")
        while not self.__stop:

            logger.debug(f"User has control: {self.user_has_control}")

            if self.user_has_control:
                self.wait_for_user_control_release()
                self.reset()

            logger.debug(f"Current state: {self.state_manager.state}")
            if self.state_manager.state != DisplayState.SCREENSAVER:
                self.display_current_menu_image()

            if self.state_manager.state == DisplayState.RUNNING_ACTION:
                self.handle_action()
                continue

            self.handle_active_time()

            if self.time_since_last_active < self.TIMEOUTS[DisplayState.SCREENSAVER]:
                continue

            if self.state_manager.state == DisplayState.DIM:
                logger.info("Starting screensaver...")
                self.state_manager.state = DisplayState.SCREENSAVER

            if self.state_manager.state == DisplayState.SCREENSAVER:
                self.show_screensaver_frame()

    def show_screensaver_frame(self):
        self.display(self.screensaver.image.convert("1"), wake=False)

    def set_is_user_controlled(self, user_has_control):
        if self.user_has_control and not user_has_control:
            self.user_gave_back_control_event.set()

        logger.info(
            f"User has {'taken' if user_has_control else 'given back'} control of the miniscreen"
        )

    def wait_for_user_control_release(self):
        logger.info("User has control. Waiting for user to give control back...")
        self.user_gave_back_control_event.wait()

    def start_current_menu_action(self, _):
        logger.debug("Setting state to RUNNING_ACTION")
        self.state = DisplayState.RUNNING_ACTION

        logger.debug("Taking note of current time for start of action")
        self.state_manager.action_timer.reset()

    def display(self, image, wake=True):
        if wake:
            self.sleep_manager.wake()
        self.miniscreen.device.display(image)
        self.last_shown_image = image

    def reset(self):
        logger.info("Forcing full state refresh...")
        self.sleep_manager.wake()
        self.miniscreen.reset()
        if self.last_shown_image is not None:
            self.display(self.last_shown_image)
        logger.info("OLED control restored")
