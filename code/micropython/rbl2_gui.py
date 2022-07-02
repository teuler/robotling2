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
# 2022-07-02, v1.3 - adapted to Pimoroni MicroPython v1.19 display API
# ----------------------------------------------------------------------------
import time
import gc
from micropython import const
from robotling_lib.misc.pulse_pixel_led import PulsePixelLED
import rbl2_global as glb
import rbl2_config as cfg

# pylint: disable=bad-whitespace
__version__    = "0.1.3.0"
BACKLIGHT      = 0.8
FONT_SIZE1     = const(2)
FONT_SIZE2     = const(3)
FONT_Y_OFFS1   = const(14)
FONT_Y_OFFS2   = const(22)
PAN_INFO_X     = const(1)
PAN_INFO_Y     = const(1)
PAN_SENS_Y     = const(2)
PAN_SENS_W     = const(80)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class GUI(object):
  """GUI"""

  def __init__(self):
    # Initializing ...
    if cfg.DISPLAY_TYPE == cfg.PIMORONI_PICO_DISPLAY:
      # Initialize RGB LED on the Pico Display breakout and display itself
      # (Display defaults to PEN_RGB332 = 256 colors)
      from pimoroni import RGBLED, Button
      from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
      self._rgbLED = RGBLED(cfg.LED_R_PIN, cfg.LED_G_PIN, cfg.LED_B_PIN)
      self._BtnA = Button(cfg.BTN_A_PIN)
      self._BtnB = Button(cfg.BTN_B_PIN)
      self._BtnX = Button(cfg.BTN_X_PIN)
      self._BtnY = Button(cfg.BTN_Y_PIN)
      self._display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
    else:
      assert False, "Display type not recognized"

    self._Pixel = PulsePixelLED(self._rgbLED.set_rgb, n_steps=cfg.PULSE_STEPS)
    self._Pixel.dim(0.6)
    self._dx, self._dy = self._display.get_bounds()
    self.clear()

  def deinit(self):
    self.clear()
    self.on(False)

  def _set_pen(self, rgb):
    p = self._display.create_pen(rgb[0], rgb[1], rgb[2])
    self._display.set_pen(p)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def display(self):
    return self._display

  @property
  def LED(self):
    return self._Pixel

  def on(self, value):
    bl = BACKLIGHT if value else 0
    self._display.set_backlight(bl)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def clear(self, only_display=False):
    """ Switch everything off
    """
    if not only_display:
      self._Pixel.RGB = (0,0,0)
    self._set_pen(cfg.COL_BKG_LO)
    self._display.clear()
    self._display.update()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def show_version(self):
    """ Show version etc.
    """
    y = 1
    self._set_pen(cfg.COL_TXT_LO)
    s = "{0} v{1:.1f}".format(cfg.RBL2_INFO, cfg.RBL2_VERSION)
    self._display.text(s, 2, y, 200, FONT_SIZE1)
    y += FONT_Y_OFFS1
    if cfg.HW_CORE == 0:
      self._display.text("core 0 only", 2, y, 200, FONT_SIZE1)
    else:
      self._set_pen(cfg.COL_TXT_OTHER)
      self._display.text("cores 0+1", 2, y, 200, FONT_SIZE1)
    self._display.update()

  def show_general_info(self, sState, sExt="", vbus=False, power_V=0):
    """ Show general info
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y +FONT_Y_OFFS1 *2
    w = self._dx -PAN_SENS_W -2
    h = FONT_Y_OFFS2 *4 -1
    try:
      # Clear part of screen
      self._display.set_clip(x, y, w, h)
      self._set_pen(cfg.COL_BKG_HI)
      self._display.clear()

      # Show state info
      self._set_pen(cfg.COL_TXT)
      self._display.text(sState, x,y, 100, FONT_SIZE2)
      y += FONT_Y_OFFS2
      if len(sExt) > 0:
        self._display.text(sExt, x,y, 100, FONT_SIZE2)
      y += FONT_Y_OFFS2

      # Show power info
      if vbus:
        self._set_pen(cfg.COL_TXT_OTHER)
      s = "ok" if vbus else "n/a"
      self._display.text(f"VBUS={s}", x,y, 100, FONT_SIZE2)

      y += FONT_Y_OFFS2
      self._set_pen(cfg.COL_TXT)
      if power_V < 3.8:
        self._set_pen(cfg.COL_TXT_WARN)
      s = "{0:.1f}V".format(power_V) if power_V > 0 else "n/a"
      self._display.text(f"VBAT={s}", x,y, 100, FONT_SIZE2)

    finally:
      self._display.update()
      self._display.remove_clip()

  def show_msg(self, msg):
    """ Show a message
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y +FONT_Y_OFFS1 *2 +FONT_Y_OFFS2 *4 -2
    w = self._dx -PAN_SENS_W -2
    h = FONT_Y_OFFS2 +2
    try:
      # Clear part of screen
      self._display.set_clip(x, y, w, h)
      self._set_pen(cfg.COL_BKG_LO)
      self._display.clear()

      # Show message
      self._set_pen(cfg.COL_TXT)
      self._display.text(msg, x,y, 100, FONT_SIZE2)

    finally:
      self._display.update()
      self._display.remove_clip()

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
      self._display.set_clip(x, y, w, h)
      self._set_pen(cfg.COL_BKG_LO)
      self._display.clear()

      # Draw a bar for each channel
      for i in range(nCh):
        s = "{0}".format(dist[i])
        if dist[i] < 0:
          s = "n/a"
          ws = 0
          ctxt = cfg.COL_TXT_LO
          self._set_pen(cfg.COL_TXT_WARN)
        elif dist[i] == dmax:
          ws = w -2
          ctxt = cfg.COL_TXT_HI
          self._set_pen(cfg.COL_TXT_WARN)
        else:
          ws = int(min(dist[i], dmax) /dmax *(w-2))
          ctxt = cfg.COL_TXT_HI
          self._set_pen(cfg.COL_TXT_LO)

        self._display.rectangle(x+1, y+i*dy+1, ws, dy-2)
        self._set_pen(ctxt)
        self._display.text(s, x+4, y+7 +i*dy, 100, FONT_SIZE2)

    finally:
      self._display.update()
      self._display.remove_clip()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def spin(self):
    self._Pixel.spin()

# ----------------------------------------------------------------------------
