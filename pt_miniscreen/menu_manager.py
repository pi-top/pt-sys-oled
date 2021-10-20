import logging
from threading import Event

from .config import menu_config
from .event import AppEvents, subscribe

logger = logging.getLogger(__name__)


class MenuManager:
    SCROLL_PX_RESOLUTION = 2

    def __init__(self, miniscreen, page_redraw_speed, scroll_speed, skip_speed):
        self._ms = miniscreen

        self.page_redraw_speed = page_redraw_speed
        self.scroll_speed = scroll_speed
        self.skip_speed = skip_speed

        self.is_skipping = False

        # self._ms.up_button.when_released = self.set_page_to_previous
        # self._ms.down_button.when_released = self.set_page_to_next
        # self._ms.select_button.when_released = self.handle_select_btn
        # self._ms.cancel_button.when_released = self.handle_cancel_btn

        def get_menu_cls(menu_cls_id):
            return menu_config[menu_cls_id].menu_cls

        self.menus = {
            "hud": get_menu_cls("hud")(miniscreen, page_redraw_speed),
            "settings": get_menu_cls("settings")(
                miniscreen,
                page_redraw_speed,
            ),
        }

        self.active_menu_id = "hud"
        self.page_has_changed = Event()

        self.setup_event_triggers()

    @property
    def active_menu(self):
        return self.menus[self.active_menu_id]

    def setup_event_triggers(self):
        def soft_transition_to_last_page(_):
            if self.active_menu_id != "hud":
                return

            last_page_index = len(self.active_menu.pages) - 1
            # Only do automatic update if on previous page
            if self.menus["hud"].page_index == last_page_index - 1:
                self.menus["hud"].page_index = last_page_index

        subscribe(AppEvents.READY_TO_BE_A_MAKER, soft_transition_to_last_page)

        def hard_transition_to_connect_page(_):
            self.active_menu_id = "hud"
            self.active_menu.page_index = len(self.active_menu.pages) - 2
            self.is_skipping = True

        subscribe(
            AppEvents.USER_SKIPPED_CONNECTION_GUIDE, hard_transition_to_connect_page
        )

    def handle_select_btn(self):
        if self.active_menu_id == "hud":
            self.set_page_to_next()
        else:
            self.active_menu.current_page.on_select_press()

        self.page_has_changed.set()

    def handle_cancel_btn(self):
        if self.active_menu_id == "hud":
            self.active_menu_id = "settings"
            self.active_menu.move_to_page(0)
        else:
            self.active_menu_id = "hud"

        self.page_has_changed.set()

    def get_page(self, index):
        return self.active_menu.pages[index]

    @property
    def page(self):
        return self.get_page(self.active_menu.page_index)

    @property
    def needs_to_scroll(self):
        y_pos = self.active_menu.y_pos
        correct_y_pos = self.active_menu.page_index * self.page.height

        return y_pos != correct_y_pos

    def set_page_to_previous(self):
        if self.needs_to_scroll:
            return

        previous_index = self.active_menu.page_index
        self.active_menu.set_page_to_previous()
        logger.debug(f"Page index: {previous_index} -> {self.active_menu.page_index}")

        self.page_has_changed.set()

    def set_page_to_next(self):
        if self.needs_to_scroll:
            return

        previous_index = self.active_menu.page_index
        self.active_menu.set_page_to_next()
        logger.debug(f"Page index: {previous_index} -> {self.active_menu.page_index}")

        self.page_has_changed.set()

    def display_current_menu_image(self):
        self._ms.device.display(self.active_menu.image)

    def wait_until_timeout_or_page_has_changed(self):
        if self.needs_to_scroll:
            if self.is_skipping:
                interval = self.skip_speed
            else:
                interval = self.scroll_speed
        else:
            interval = self.page_redraw_speed

        self.page_has_changed.wait(interval)
        if self.page_has_changed.is_set():
            self.page_has_changed.clear()

    def update_scroll_position(self):
        if not self.needs_to_scroll:
            self.is_skipping = False
            return

        correct_y_pos = self.active_menu.page_index * self._ms.size[1]
        move_down = correct_y_pos > self.active_menu.y_pos

        self.active_menu.y_pos += self.SCROLL_PX_RESOLUTION * (1 if move_down else -1)
