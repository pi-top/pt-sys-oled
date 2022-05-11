import logging
from threading import Event, Thread
from time import sleep

from PIL import Image

from ..utils import carousel
from .text import Text

logger = logging.getLogger(__name__)


class MarqueeText(Text):
    def cleanup(self):
        if self._stop_scroll_event:
            self._stop_scroll_event.set()

    def __init__(
        self,
        step=1,
        step_time=0.1,
        initial_state={},
        wrap=None,  # take wrap out of kwargs
        **kwargs
    ):
        super().__init__(
            **kwargs,
            wrap=False,
            initial_state={
                **initial_state,
                "offset": 0,
                "step": step,
                "step_time": step_time,
            },
        )

        self._stop_scroll_event = None

    @property
    def needs_scrolling(self) -> bool:
        text_size = self.get_text_size(self.state["text"], self.state["font"])
        return self.width < text_size[0]

    @property
    def scrolling(self) -> bool:
        return self._stop_scroll_event and not self._stop_scroll_event.is_set()

    def _start_scrolling(self):
        if not self.scrolling:
            self._stop_scroll_event = Event()
            Thread(
                target=self._scroll, args=[self._stop_scroll_event], daemon=True
            ).start()

    def _scroll(self, stop_event):
        text_size = self.get_text_size(self.state["text"], self.state["font"])
        scroll_len = max(text_size[0] - self.width, 0)

        for offset in carousel(scroll_len, step=self.state["step"]):
            sleep(self.state["step_time"])
            if stop_event.is_set():
                return

            self.state.update({"offset": -offset})

    def render(self, image):
        if not self.scrolling and self.needs_scrolling:
            self._start_scrolling()

        if self.scrolling and not self.needs_scrolling:
            self._stop_scroll_event.set()

        text_size = self.get_text_size(self.state["text"], self.state["font"])
        offset = self.state["offset"] if self.needs_scrolling else 0

        image.paste(
            super().render(Image.new("1", size=(text_size[0], image.height))),
            (offset, 0),
        )
        return image