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
from machine import Pin, PWM, I2C
import micropython
from robotling_lib.misc.pulse_pixel_led import PulsePixelLED
#import picodisplay as _display
import WaveshareLCD
import rbl2_global as glb
import rbl2_config as cfg
import utime
from vl53l0x import setup_tofl_device, TBOOT

# pylint: disable=bad-whitespace
__version__    = "0.1.0.0"
BACKLIGHT      = const(52428) # 80% Backlight
FONT_SIZE1     = const(2)
FONT_SIZE2     = const(3)
FONT_Y_OFFS1   = const(14)
FONT_Y_OFFS2   = const(22)
PAN_INFO_X     = const(2)
PAN_INFO_Y     = const(2)
PAN_SENS_Y     = const(2)
PAN_SENS_W     = const(80)

# pylint: enable=bad-whitespace
class GUI(object):
  """GUI"""

  def __init__(self):
     global PicoDisplay
     global LED
       
       
     PicoDisplay = WaveshareLCD.LCD_1inch14()
     LED = PWM (Pin(19))
     LED.freq (1000)
     # Initializing ...
     self._dx = PicoDisplay.get_width()
     self._dy = PicoDisplay.get_height()
     PicoDisplay.init_display ()
     self._Pixel = PulsePixelLED(self.set_led, n_steps=cfg.PULSE_STEPS)
     self._Pixel.dim(0.6)
     self.clear()
 
 
  def deinit(self):
    self.clear()
    self.on(False)
#    print ("Ende")

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def display(self):
    return PicoDisplay

  @property
  def LED(self):
    return self._Pixel


  def set_led(self, r, g, b):
      LED.duty_u16 (max([r, g, b])*256)

  def on(self, value):
      if (value == True):
          value = 32768
      PicoDisplay.SetBL (value)
        
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def clear(self, only_display=False):
      """ Switch everything off
      """
#      print("--------------------")
      if not only_display:
          self._Pixel.RGB = (0,0,0)
          PicoDisplay.fill(cfg.COL_BKG_LO)
          PicoDisplay.show()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def show_version(self):
    """ Show version etc.
    """

    y = 2
    s = "{0} v{1:.1f}".format(cfg.RBL2_INFO, cfg.RBL2_VERSION)
#    print (s)
    PicoDisplay.text (s, 2, y, cfg.COL_TXT_LO)
    y += FONT_Y_OFFS1
    if cfg.HW_CORE == 0:
        PicoDisplay.text ("core 0 only", 2, y, cfg.COL_TXT_LO)
#       print ("core 0 only")
    else:
#       print ("core 0+1")
       PicoDisplay.text("cores 0+1", 2, y, cfg.COL_TXT_OTHER)
    PicoDisplay.show()

  def show_general_info(self, sState, sExt="", vbus=False, power_V=0):
    """ Show general info
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y +FONT_Y_OFFS1 *2
    w = self._dx -PAN_SENS_W -2
    h = FONT_Y_OFFS2 *3 -1
    try:
      # Clear part of screen
      # _display.set_clip(x, y, w, h)
      PicoDisplay.fill_rect (x, y, w, h, cfg.COL_BKG_LO)
      
      # Show state info
      PicoDisplay.text (sState, x,y, cfg.COL_TXT)
#     print (sState)
      y += FONT_Y_OFFS2
      if len(sExt) > 0:
#        print (sExt)
        PicoDisplay.text (sExt, x,y, cfg.COL_TXT)
      y += FONT_Y_OFFS2

      # Show power info
      PicoDisplay.text ("VBUS" if vbus else " -- ", x,y, cfg.COL_TXT_OTHER)
      x = 80
      s = "{0:.1f}V".format(power_V) if power_V > 0 else " -- "
      _Col = cfg.COL_TXT
      if power_V < 2:
        _Col = cfg.COL_TXT_WARN
#    print (s)
      PicoDisplay.text (s, x,y, _Col)

    finally:
      PicoDisplay.show ()

  def show_msg(self, msg):
    """ Show a message
    """
    x = PAN_INFO_X
    y = PAN_INFO_Y + FONT_Y_OFFS1 * 2 + FONT_Y_OFFS2 * 3
    w = self._dx - PAN_SENS_W - 2
    h = FONT_Y_OFFS2 + 2
    try:
      # Clear part of screen
      PicoDisplay.fill_rect (x, y, w, h, cfg.COL_BKG_LO)
            
      # Show message
      PicoDisplay.text (msg, x,y, cfg.COL_TXT)

    finally:
      PicoDisplay.show()
 
#   def show_distance_evo(self, dist):
#     """ Show distance info from evo mini sensor
#     """
#     x = self._dx -PAN_SENS_W +1
#     y = PAN_SENS_Y
#     w = PAN_SENS_W -1
#     h = self._dy
#     dy = h //4
#     try:
#       # Clear part of screen
#       PicoDisplay.SetPen2 (cfg.COL_BKG_LO)
#       PicoDisplay.LCDfillrect (x, y, w, h)
# 
#       for i in range(4):
#         s = "{0}".format(dist[i])
#         if dist[i] < 0:
#           s = "n/a"
#           ws = 0
#           ctxt = cfg.COL_TXT_LO
#           PicoDisplay.SetPen2 (cfg.COL_TXT_WARN)
#         elif dist[i] == cfg.EVOMINI_MAX_MM:
#           ws = w -2
#           ctxt = cfg.COL_TXT_HI
#           PicoDisplay.SetPen2 (cfg.COL_TXT_WARN)
#         else:
#           ws = int(min(dist[i], cfg.EVOMINI_MAX_MM) /cfg.EVOMINI_MAX_MM *(w-2))
#           ctxt = cfg.COL_TXT_HI
#           PicoDisplay.SetPen2 (cfg.COL_TXT_LO)
#         PicoDisplay.LCDfillrect(x+1, y+i*dy+1, ws, dy-2)
#         PicoDisplay.SetPen2 (ctxt)
#         PicoDisplay.LCDText (s, x+30, y+13 +i*dy, 100, FONT_SIZE2)
# 
#     finally:
#       PicoDisplay.show()
# 

  def show_distance_tof(self, dist):
    """ Show distance info from evo mini sensor
    """
    x = self._dx -PAN_SENS_W +1
    y = PAN_SENS_Y
    w = PAN_SENS_W -1
    h = self._dy
    dy = h // 3
    try:
      # Clear part of screen
      PicoDisplay.fill_rect (x, y, w, h, cfg.COL_BKG_LO)
      
      for i in range(3):
        s = "{0}".format(dist[i])
        if dist[i] < 0:
          s = "n/a"
          ws = 0
          _ctxt = cfg.COL_TXT_LO
          _cbkg = cfg.COL_TXT_WARN
        elif dist[i] > cfg.TOF_MAX_MM:
          ws = w - 2
          _ctxt = cfg.COL_TXT_HI
          _cbkg = cfg.COL_TXT_WARN
        else:
          ws = int(min(dist[i], cfg.TOF_MAX_MM) / cfg.TOF_MAX_MM *(w-2))
          _ctxt = cfg.COL_TXT_HI
          _cbkg = cfg.COL_TXT_LO
        PicoDisplay.fill_rect (x+1, y+i*dy+1, ws, dy-2, _cbkg)
        PicoDisplay.text (s, x+30, y+19 +i*dy, _ctxt)

    finally:
      PicoDisplay.show()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def spin(self):
    self._Pixel.spin()

#----------------------------------------------------------------------------

if __name__=='__main__':
    def PrintAddresses (i2c):
        addresses = i2c.scan()
        for address in addresses:
          print (hex(address))
    
    micropython.mem_info()
    RobotGUI = GUI()
    micropython.mem_info()
    RobotGUI.show_version()
    RobotGUI.show_general_info("Forward", "1", False, 2.0)
    RobotGUI.show_msg ("Test")
#   RobotGUI.show_distance_evo ([-1,100, 250, 500])
#   RobotGUI.show_distance_tof ([200,5000, 8400])
    RobotGUI.spin()
    RobotGUI.LED.startPulse(150)
    RobotGUI.LED.RGB = (0, 0, 60)
    RobotGUI.display.is_pressed (RobotGUI.display.BUTTON_B)

    device_1_xshut = Pin(3, Pin.OUT)
    device_2_xshut = Pin(22, Pin.OUT)
    device_1_xshut.value(1)
    device_2_xshut.value(1)
    utime.sleep_us (1200)

    i2c = I2C(id=0, sda=Pin(0), scl=Pin(1))
    PrintAddresses(i2c)
    addresses =i2c.scan()
    if (not (0x31 in addresses)):
        print("Setting up device 0")
        device_1_xshut.value(0)
        device_2_xshut.value(0)
        tofl0 = setup_tofl_device(i2c, 40000, 12, 8)
        tofl0.set_address(0x31)
    else:
        print("Reconnect device 0")
        device_1_xshut.value(0)
        device_2_xshut.value(0)
        PrintAddresses(i2c)
        tofl0 = setup_tofl_device(i2c, 40000, 12, 8, 0x31)

    if (not (0x33 in addresses)):
        print("Setting up device 1")
        device_1_xshut.value(1)
        device_2_xshut.value(0)
        utime.sleep_us(TBOOT)
        tofl1 = setup_tofl_device(i2c, 40000, 12, 8)
        tofl1.set_address(0x33)
    else:
        print("Reconnect device 1")
        device_1_xshut.value(1)
        device_2_xshut.value(0)
        utime.sleep_us(TBOOT)
        tofl1 = setup_tofl_device(i2c, 40000, 12, 8, 0x33)

    if (0x29 in addresses):
        print("Now setting up device 2")
        # Re-enable device 2 - on the same bus
        device_1_xshut.value(1)
        device_2_xshut.value(1)
        utime.sleep_us(TBOOT)
        tofl2 = setup_tofl_device(i2c, 40000, 12, 8)
    else:
        print("!!!!Fehler!!!")
        
    try:
        PrintAddresses(i2c)
        while True:
            RobotGUI.spin()
            center, right, left = tofl0.ping(), tofl1.ping(), tofl2.ping()
            RobotGUI.show_distance_tof ([left, center, right])

    finally:
        print("Restoring")
        tofl0.set_address(0x29)
        tofl1.set_address(0x29)

