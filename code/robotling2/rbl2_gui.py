# ----------------------------------------------------------------------------
# rbl2_gui.py
#
# GUI at startup
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-03-28, v1.0
# ----------------------------------------------------------------------------
import time
import gc
from micropython import const
from robotling_lib.misc.pulse_pixel_led import PulsePixelLED
import picodisplay as _display
import rbl2_global as glb
import rbl2_config as cfg

# pylint: disable=bad-whitespace
__version__    = "0.1.0.0"
BACKLIGHT      = 0.8
FONT_SIZE1     = const(2)
FONT_SIZE2     = const(3)
FONT_Y_OFFS1   = const(14)
FONT_Y_OFFS2   = const(22)

BUFFER         = bytearray(_display.get_width() *_display.get_height() *2)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class GUI(object):
  """GUI"""

  def __init__(self):
    global BUFFER

    # Initializing ...
    self._dx = _display.get_width()
    self._dy = _display.get_height()
    _display.init(BUFFER)
    #_display.flip()
    self._Pixel = PulsePixelLED(_display.set_led, n_steps=cfg.PULSE_STEPS)
    self._Pixel.dim(0.6)
    self.clear()

  def deinit(self):
    self.clear()
    self.on(False)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def display(self):
    return _display

  @property
  def LED(self):
    return self._Pixel

  def on(self, value):
    bl = BACKLIGHT if value else 0
    _display.set_backlight(bl)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def clear(self, only_display=False):
    """ Switch everything off
    """
    if not only_display:
      self._Pixel.RGB = (0,0,0)
    _display.set_pen(0, 0, 0)
    _display.clear()
    _display.update()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def show_version(self):
    """ Show version etc.
    """
    y = 2
    _display.set_pen(cfg.COL_TXT_HI)
    s = "{0} v{1:.1f}".format(cfg.RBL2_INFO, cfg.RBL2_VERSION)
    _display.text(s, 2, y, 200, FONT_SIZE1)
    y += FONT_Y_OFFS1
    if cfg.HW_CORE == 0:
      _display.text("core 0 only", 2, y, 200, FONT_SIZE1)
    else:
      _display.set_pen(cfg.COL_TXT_RED)
      _display.text("cores 0+1", 2, y, 200, FONT_SIZE1)
    _display.update()

  def show_info(self, sState, sExt=""):
    """ Show info
    """
    x = 2
    y = 2 +FONT_Y_OFFS1 *2
    w = self._dx -80
    h = self._dy
    try:
      # Clear part of screen
      _display.set_clip(x, y, w, h)
      _display.set_pen(cfg.COL_BKG_LO)
      _display.clear()

      # Show state info
      _display.set_pen(cfg.COL_TXT_LO)
      _display.text(sState, x,y, 100, FONT_SIZE2)
      if len(sExt) > 0:
        y += FONT_Y_OFFS2
        _display.text(sExt, x,y, 100, FONT_SIZE2)

    finally:
      _display.update()
      _display.remove_clip()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def spin(self):
    self._Pixel.spin()

# ----------------------------------------------------------------------------
