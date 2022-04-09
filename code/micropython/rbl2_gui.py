# ----------------------------------------------------------------------------
# rbl2_gui.py
#
# GUI at startup
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-03-28, v1.0
# 2022-02-12, v1.1
# 2022-04-08, v1.2
# ----------------------------------------------------------------------------
import time
import gc
from micropython import const
from robotling_lib.misc.pulse_pixel_led import PulsePixelLED
import rbl2_global as glb
import rbl2_config as cfg

if "display" in cfg.DEVICES:
  if cfg.DISPLAY_TYPE == cfg.PIMORONI_PICO_DISPLAY:
    import picodisplay as _display
    DSP_WIDTH = const(240)
    DSP_HEIGHT = const(135)
  else:
    assert False, "Display type not recognized"
  BUFFER = bytearray(DSP_WIDTH *DSP_HEIGHT *2)
else:
  _display = None   

# pylint: disable=bad-whitespace
__version__    = "0.1.2.0"
BACKLIGHT      = 0.8
FONT_SIZE1     = const(2)
FONT_SIZE2     = const(3)
FONT_Y_OFFS1   = const(14)
FONT_Y_OFFS2   = const(22)
PAN_INFO_X     = const(2)
PAN_INFO_Y     = const(2)
PAN_SENS_Y     = const(2)
PAN_SENS_W     = const(80)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class GUI(object):
  """GUI"""

  def __init__(self):
    global BUFFER

    # Initializing ...
    self._dx = DSP_WIDTH
    self._dy = DSP_HEIGHT
    _display.init(BUFFER)
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
    _display.set_pen(cfg.COL_TXT_LO)
    s = "{0} v{1:.1f}".format(cfg.RBL2_INFO, cfg.RBL2_VERSION)
    _display.text(s, 2, y, 200, FONT_SIZE1)
    y += FONT_Y_OFFS1
    if cfg.HW_CORE == 0:
      _display.text("core 0 only", 2, y, 200, FONT_SIZE1)
    else:
      _display.set_pen(cfg.COL_TXT_OTHER)
      _display.text("cores 0+1", 2, y, 200, FONT_SIZE1)
    _display.update()

  def show_general_info(self, sState, sExt="", vbus=False, power_V=0):
    """ Show general info
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y +FONT_Y_OFFS1 *2
    w = self._dx -PAN_SENS_W -2
    h = FONT_Y_OFFS2 *3 -1
    try:
      # Clear part of screen
      _display.set_clip(x, y, w, h)
      _display.set_pen(cfg.COL_BKG_LO)
      _display.clear()

      # Show state info
      _display.set_pen(cfg.COL_TXT)
      _display.text(sState, x,y, 100, FONT_SIZE2)
      y += FONT_Y_OFFS2
      if len(sExt) > 0:
        _display.text(sExt, x,y, 100, FONT_SIZE2)
      y += FONT_Y_OFFS2

      # Show power info
      if vbus:
        _display.set_pen(cfg.COL_TXT_OTHER)
      _display.text("VBUS" if vbus else " -- ", x,y, 100, FONT_SIZE2)
      _display.set_pen(cfg.COL_TXT)
      if power_V < 2:
        _display.set_pen(cfg.COL_TXT_WARN)
      x = 80
      s = "{0:.1f}V".format(power_V) if power_V > 0 else " -- "
      _display.text(s, x,y, 100, FONT_SIZE2)

    finally:
      _display.update()
      _display.remove_clip()

  def show_msg(self, msg):
    """ Show a message
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y +FONT_Y_OFFS1 *2 +FONT_Y_OFFS2 *3
    w = self._dx -PAN_SENS_W -2
    h = FONT_Y_OFFS2 +2
    try:
      # Clear part of screen
      _display.set_clip(x, y, w, h)
      _display.set_pen(cfg.COL_BKG_LO)
      _display.clear()

      # Show message
      _display.set_pen(cfg.COL_TXT)
      _display.text(msg, x,y, 100, FONT_SIZE2)

    finally:
      _display.update()
      _display.remove_clip()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def show_distance_evo(self, dist):
    """ Show distance info from evo mini sensor
    """
    self._show_dist(dist, cfg.EVOMINI_MIN_MM, cfg.EVOMINI_MAX_MM)

  def show_distance_tof(self, dist):
    """ Show distance info from 3-channel tof sensor array
    """
    self._show_dist(dist, cfg.TOFPWM_MIN_MM, cfg.TOFPWM_MAX_MM)
    
  def _show_dist(self, dist, dmin, dmax):
    """ Show distance
    """
    x = self._dx -PAN_SENS_W +1
    y = PAN_SENS_Y
    w = PAN_SENS_W -1
    h = self._dy
    nCh = len(dist)
    dy = h //nCh
    try:
      # Clear part of screen
      _display.set_clip(x, y, w, h)
      _display.set_pen(cfg.COL_BKG_LO)
      _display.clear()

      # Draw a bar for each channel
      for i in range(nCh):
        s = "{0}".format(dist[i])
        if dist[i] < 0:
          s = "n/a"
          ws = 0
          ctxt = cfg.COL_TXT_LO
          _display.set_pen(cfg.COL_TXT_WARN)
        elif dist[i] == dmax:
          ws = w -2
          ctxt = cfg.COL_TXT_HI
          _display.set_pen(cfg.COL_TXT_WARN)
        else:
          ws = int(min(dist[i], dmax) /dmax *(w-2))
          ctxt = cfg.COL_TXT_HI
          _display.set_pen(cfg.COL_TXT_LO)

        _display.rectangle(x+1, y+i*dy+1, ws, dy-2)
        _display.set_pen(ctxt)
        _display.text(s, x+4, y+7 +i*dy, 100, FONT_SIZE2)

    finally:
      _display.update()
      _display.remove_clip()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def spin(self):
    self._Pixel.spin()

# ----------------------------------------------------------------------------
