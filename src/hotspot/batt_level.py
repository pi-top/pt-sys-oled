#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-18 Richard Hull and contributors
# See LICENSE.rst for details.

import time
from luma.core.virtual import hotspot
import os
import subprocess

def render(draw, width, height):
    battery_percentage = subprocess.Popen(["pt-battery", "-c"], stdout=subprocess.PIPE).communicate()[0]

    percentage = "batt_level:" + battery_percentage + "%"
    draw.text((width/10, height/10), text=percentage, fill="white")

class Battery_level(hotspot):

    def __init__(self, width, height, interval):
        super(Battery_level, self).__init__(width, height)
        self._interval = interval
        self._last_updated = 0

    def should_redraw(self):
        return time.time() - self._last_updated > self._interval

    def update(self, draw):
        render(draw, self.width, self.height)
        self._last_updated = time.time()
