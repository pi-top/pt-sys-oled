import logging

from pt_miniscreen.core.hotspot import Hotspot
from pt_miniscreen.core.hotspots.image import Image
from pt_miniscreen.core.utils import apply_layers, layer, rectangle

logger = logging.getLogger(__name__)


class RightGutter(Hotspot):
    def __init__(
        self,
        upper_icon_path=None,
        lower_icon_path=None,
        upper_icon_padding=(0, 0),
        lower_icon_padding=(0, 0),
        **kwargs
    ):
        super().__init__(
            **kwargs,
            initial_state={
                "upper_icon_padding": upper_icon_padding,
                "lower_icon_padding": lower_icon_padding,
            },
        )

        self.upper_icon = self.create_hotspot(Image, image_path=upper_icon_path)
        self.lower_icon = self.create_hotspot(Image, image_path=lower_icon_path)

    def render(self, image):
        border_width = 1
        left_border_layer = layer(rectangle, size=(border_width, image.height))
        layers = [left_border_layer]

        if self.upper_icon.image:
            layers.append(
                layer(
                    self.upper_icon.render,
                    size=self.upper_icon.image.size,
                    pos=self.state["upper_icon_padding"],
                )
            )

        if self.lower_icon.image:
            icon_size = self.lower_icon.image.size
            icon_padding = self.state["lower_icon_padding"]
            icon_pos = (icon_padding[0], image.height - icon_size[1] - icon_padding[1])

            layers.append(layer(self.lower_icon.render, size=icon_size, pos=icon_pos))

        return apply_layers(image, layers)
