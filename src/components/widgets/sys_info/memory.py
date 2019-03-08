# Copyright (c) 2014-18 Richard Hull and contributors
# See LICENSE.rst for details.

import psutil
from ptcommon.formatting import bytes2human
from components.widgets.common_functions import right_text, title_text, draw_text
from components.widgets.common_values import default_margin_x
from components.widgets.common.base_widget_hotspot import BaseHotspot


class Hotspot(BaseHotspot):
    def __init__(self, width, height, interval, **data):
        super(Hotspot, self).__init__(width, height, interval, Hotspot.render)

    @staticmethod
    def render(draw, width, height):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        mem_used_pct = (mem.total - mem.available) * 100.0 / mem.total

        title_text(draw, y=default_margin_x, width=width, text="Memory")
        draw_text(draw, xy=(default_margin_x, height / common_first_line_y), text="Used:")
        draw_text(draw, xy=(default_margin_x, height / common_second_line_y), text="Phys:")
        draw_text(draw, xy=(default_margin_x, height / common_third_line_y), text="Swap:")

        right_text(draw, height / common_first_line_y, width, text="{0:0.1f}%".format(mem_used_pct))
        right_text(draw, height / common_second_line_y, width, text=bytes2human(mem.used))
        right_text(draw, height / common_third_line_y, width, text=bytes2human(swap.used))
