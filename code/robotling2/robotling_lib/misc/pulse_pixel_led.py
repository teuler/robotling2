# ----------------------------------------------------------------------------
# pulse_pixel_led.py
# Generic pulsing of a Pixel/RGB LED
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-04-06, v1
# ----------------------------------------------------------------------------
import array
from robotling_lib.misc.color_wheel import getColorFromWheel

# ----------------------------------------------------------------------------
class PulsePixelLED(object):
  """To pulse a pixel/RGB LED"""

  def __init__(self, func_set_rgb, n_steps=10):

    self._iColor = 0
    self._RGB = bytearray([0]*3)
    self._curr = array.array("i", [0,0,0])
    self._step = array.array("i", [0,0,0])
    self._fact = 1.0
    self._pulse = False
    self._set_rgb = func_set_rgb
    self._enablePulse = True
    self._nSteps = n_steps

  @property
  def RGB(self):
    return self._RGB

  @RGB.setter
  def RGB(self, value):
    """ Set color of RGB LEDs ("Pixel") by assigning a RGB value or a color
        wheel index (and stop pulsing, if running)
    """
    try:
      r, g, b = value
    except TypeError:
      r, g, b = getColorFromWheel(value)
    self._set_rgb(r, g, b)
    self._pulse = False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def startPulse(self, value):
    """ Set color of RGB LEDs and enable pulsing
    """
    iColPrev = self._iColor
    if self._enablePulse:
      try:
        rgb = bytearray([value[0], value[1], value[2]])
      except TypeError:
        rgb = getColorFromWheel(value)
        self._iColor = value

      if (rgb != self._RGB) or not(self._pulse):
        # New color and start pulsing
        c = self._curr
        s = self._step
        n = self._nSteps
        c[0] = rgb[0]
        s[0] = int(rgb[0] /n)
        c[1] = rgb[1]
        s[1] = int(rgb[1] /n)
        c[2] = rgb[2]
        s[2] = int(rgb[2] /n)
        self._RGB = rgb
        self._set_rgb(rgb[0], rgb[1], rgb[2])
        self._pulse = True
        self._fact = 1.0
    return iColPrev

  def dim(self, factor=1.0):
    self._fact = max(min(1, factor), 0)

  def spin(self):
    """ Update pulsing, if enabled
    """
    if self._pulse:
      rgb = self._RGB
      c = self._curr
      s = self._step
      f = self._fact
      for i in range(3):
        c[i] += s[i]
        s[i] *= -1 if c[i] > (rgb[i] -s[i]) else 1
        s[i] = abs(s[i]) if c[i] < abs(s[i]) else s[i]
        c[i] = int(c[i] *f) if f < 1.0 else c[i]
        c[i] = min(c[i], 255)
      self._set_rgb(c[0], c[1], c[2])

# ----------------------------------------------------------------------------
