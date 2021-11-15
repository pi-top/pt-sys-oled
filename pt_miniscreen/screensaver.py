from dataclasses import dataclass
from random import randrange

from PIL import Image, ImageDraw


@dataclass
class Star:
    x: int
    y: int
    z: int


class StarfieldScreensaver:
    SCREENSAVER_MAX_DEPTH = 32
    SCREENSAVER_MAX_NO_OF_STARS = 512
    Z_MOVE = 0.19

    def __init__(self, mode, size):
        self.mode = mode
        self.size = size

        self.screensaver_stars = [
            Star(
                randrange(-25, 25),
                randrange(-25, 25),
                randrange(1, self.SCREENSAVER_MAX_DEPTH),
            )
            for i in range(self.SCREENSAVER_MAX_NO_OF_STARS)
        ]

    @property
    def image(self):
        # Adapted from https://github.com/rm-hull/luma.examples/blob/master/examples/starfield.py

        origin_x = self.size[0] // 2
        origin_y = self.size[1] // 2

        image = Image.new(self.mode, self.size)

        draw = ImageDraw.Draw(image)

        for star in self.screensaver_stars:
            # Move star 'closer to the display'
            star.z -= self.Z_MOVE
            # Star has moved 'past the display'
            if star.z <= 0:
                # Reposition far away from the screen (Z=max_depth)
                # with random X and Y coordinates
                star.x = randrange(-25, 25)
                star.y = randrange(-25, 25)
                star.z = self.SCREENSAVER_MAX_DEPTH

            # Convert 3D coordinates to 2D using perspective projection
            k = 128.0 / star.z
            x = int(star.x * k + origin_x)
            y = int(star.y * k + origin_y)

            # Draw star if visible
            if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                # Distant stars are smaller than closer stars
                size = (1 - float(star.z) / self.SCREENSAVER_MAX_DEPTH) * 4
                draw.rectangle((x, y, x + size, y + size), fill="white")

        return image