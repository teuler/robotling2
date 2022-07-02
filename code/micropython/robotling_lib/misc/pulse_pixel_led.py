# ----------------------------------------------------------------------------
# pulse_pixel_led.py
# Generic pulsing of a Pixel/RGB LED
#
# The MIT License (MIT)
# Copyright (c) 2021-22 Thomas Euler
# 2021-04-06, v1.0
# 2022-05-10, v1.1, Added a version that supports hue and a pixel array
# ----------------------------------------------------------------------------
import array
from robotling_lib.misc.color_wheel import getColorFromWheel

# ----------------------------------------------------------------------------
class PulsePixelLED_Hue(object):
  """To pulse a pixel/RGB LED via hue"""

  def __init__(self, func_set_hue, n_steps=10, iLED=0):
    # Expects a function with the parameters `LED index`, `hue`, `saturation`,
    # and `brighness`
    self._hue = 0.
    self._brighness = 1.0
    self._iLED = iLED
    self._pulse = False
    self._set_hue = func_set_hue
    self._enablePulse = True
    self._iStep = 0
    self._nSteps = n_steps
    self._brightnessStep = 0.0

  @property
  def hue(self):
    return self._hue

  @hue.setter
  def hue(self, value):
    """ Set color of RGB LEDs ("Pixel") by assigning a hue value (0..1)
        and stop pulsing, if running.
    """
    self._hue = min(max(value, 0), 1)
    self._set_hue(self._iLED, self._hue, 1.0, self._brighness)
    self._pulse = False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def startPulse(self, value):
    """ Set color of RGB LEDs and enable pulsing
    """
    prevHue = self._hue
    if self._enablePulse:
      newHue = min(max(value, 0), 1)
      if (self._hue -newHue) > 0.01 or not self._pulse:
        # New color and start pulsing
        self._hue = newHue
        self._iStep = 0
        self._brightnessStep = self._brighness /self._nSteps
        self._set_hue(self._iLED, self._hue, 1.0, 0)
        self._pulse = True
    return prevHue

  def dim(self, factor=1.0):
    self._brighness = max(min(1, factor), 0)

  def spin(self):
    """ Update pulsing, if enabled
    """
    if self._pulse:
      nst = self._nSteps
      ist = self._iStep
      bst = self._brightnessStep
      self._set_hue(self._iLED, self._hue, 1.0, abs(bst) *ist)
      if bst > 0:
        self._iStep += 1 if ist < nst-1 else -1
      else:
        self._iStep += -1 if ist > 0 else 1
      self._brightnessStep *= -1 if ist == 0 or ist == nst-1 else 1

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
        wheel index and stop pulsing, if running.
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
