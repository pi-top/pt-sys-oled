from .viewport import Viewport


class MenuBase:
    def __init__(
        self, size, mode, page_redraw_speed, overlay_render_func=None, children={}
    ):

        self.pages = []
        for name, config in children.items():
            self.pages.append(
                config.page_cls(
                    interval=page_redraw_speed,
                    size=size,
                    mode=mode,
                    children=config.children,
                )
            )
        self.page_index = 0

        self.viewport = Viewport(
            display_size=(size[0], size[1] * len(self.pages)),
            window_size=size,
            mode=mode,
        )

        self.overlay_render_func = overlay_render_func

        for i, page in enumerate(self.pages):
            self.viewport.add_hotspot(page, (0, i * size[1]))

    @property
    def current_page(self):
        return self.pages[self.page_index]

    @property
    def y_pos(self):
        return self.viewport._position[1]

    @y_pos.setter
    def y_pos(self, pos):
        return self.viewport.set_position((0, pos))

    def move_to_page(self, index):
        self.page_index = index
        self.y_pos = self.page_index * self.viewport.height

    @property
    def image(self):
        im = self.viewport.image.copy()

        if callable(self.overlay_render_func):
            self.overlay_render_func(im)

        return im

    def set_page_index_to(self, page_index):
        self.page_index = page_index

    def set_page_to_previous(self):
        self.set_page_index_to(self.get_previous_page_index())

    def set_page_to_next(self):
        self.set_page_index_to(self.get_next_page_index())

    def get_previous_page_index(self):
        # Return next page if at top
        if self.page_index == 0:
            return self.get_next_page_index()

        idx = self.page_index - 1
        candidate = self.pages[idx]
        return idx if candidate.visible else self.page_index

    def get_next_page_index(self):
        # Return current page if at end
        if self.page_index + 1 >= len(self.pages):
            return self.page_index

        idx = self.page_index + 1
        candidate = self.pages[idx]
        return idx if candidate.visible else self.page_index
