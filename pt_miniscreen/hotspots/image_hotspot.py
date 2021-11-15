import logging

import PIL.Image

from .base import Hotspot as HotspotBase

logger = logging.getLogger(__name__)


class Hotspot(HotspotBase):
    def __init__(self, interval, size, mode, image_path, xy=None):
        super().__init__(interval, size, mode)
        self.xy = xy
        self._im = None
        self.image_path = image_path
        self._frame_no = 0
        self.loop = True
        self.playback_speed = 1.0

    def render(self, image):
        if not self._im:
            return

        if self._im.is_animated:
            if self._frame_no + 1 < self._im.n_frames:
                self._frame_no += 1
            elif self.loop:
                self._frame_no = 0

        self._im.seek(self._frame_no)

        if self._im.is_animated:
            embedded_frame_speed_s = float(self._im.info["duration"] / 1000)
            self.interval = float(embedded_frame_speed_s / self.playback_speed)

        PIL.ImageDraw.Draw(image).bitmap(
            xy=self.xy,
            bitmap=self._im.convert(self.mode),
            fill="white",
        )

    @property
    def image(self):
        return self._im

    @property
    def image_path(self):
        return self._im_path

    @image_path.setter
    def image_path(self, path):
        self._im_path = path
        if path is None:
            return
        try:
            self._im = PIL.Image.open(path)
            if self.xy is None:
                self.xy = (
                    self.size[0] / 2 - self._im.width / 2,
                    self.size[1] / 2 - self._im.height / 2,
                )
        except Exception as e:
            logger.warning(f"Couldn't open image {path} : {e}")
            raise