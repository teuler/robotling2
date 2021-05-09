# ----------------------------------------------------------------------------
# robotling_base.py
# Definition of a base class `RobotlingBase`, from which classes that capture
# all functions and properties of a specific board
#
# The MIT License (MIT)
# Copyright (c) 2020 Thomas Euler
# 2020-09-04, v1
# 2020-10-31, v1.1, use `languageID` instead of `ID`
# 2020-12-21, v1.2, moved all RGB pixel management here
# ----------------------------------------------------------------------------
import gc
import array
from micropython import const
from robotling_lib.misc.helpers import TimeTracker
import robotling_lib.misc.ansi_color as ansi
import robotling_lib.robotling_board as rb
from robotling_lib.misc.color_wheel import getColorFromWheel

from robotling_lib.platform.platform import platform as pf
if pf.languageID == pf.LNG_MICROPYTHON:
  import time
  from robotling_lib.platform.esp32 import busio
  import robotling_lib.platform.esp32.dio as dio
  from machine import Pin
elif pf.languageID == pf.LNG_CIRCUITPYTHON:
  import robotling_lib.platform.circuitpython.time as time
  from robotling_lib.platform.circuitpython import busio
  import robotling_lib.platform.circuitpython.dio as dio
else:
  print(ansi.RED +"ERROR: No matching libraries in `platform`." +ansi.BLACK)

__version__      = "0.1.2.0"

# ----------------------------------------------------------------------------
class RobotlingBase(object):
  """Robotling base class.

  Objects:
  -------
  - onboardLED     : on(), off()

  Methods:
  -------
  - connectToWLAN():
    Connect to WLAN if not already connected

  - updateStart(), updateEnd()
    To be called at the beginning and the end of an update routine
  - spin_ms(dur_ms=0, period_ms=-1, callback=None)
    Instead of using a timer that calls `update()` at a fixed frequency (e.g.
    at 20 Hz), one can regularly, calling `spin()` once per main loop and
    everywhere else instead of `time.sleep_ms()`. For details, see there.
  - spin_while_moving(t_spin_ms=50)
    Call spin frequently while waiting for the current move to finish

  - startPulsePixel()
    Set color of RGB pixel and enable pulsing

  - printReport()
    Print statistics of the last run into the history
  - powerDown()
    To be called when the robot shuts down; to be overwritten

  Properties:
  ----------
  - memory         : Returns allocated and free memory as tuple
  - PixelRGB       : get and set color (r,g,b tuple or color wheel index)
  - dotStarPower   : Turns power to DotStar LED, if any, on or off

  Internal objects:
  ----------------
  - _MCP3208       : 8-channel 12-bit A/C converter driver

  Internal methods:
  ----------------
  - _pulsePixel()
    Update pulsing, if enabled
  """
  MIN_UPDATE_PERIOD_MS = const(20)  # Minimal time between update() calls
  APPROX_UPDATE_DUR_MS = const(8)   # Approx. duration of the update/callback
  HEARTBEAT_STEPS      = const(10)  # Number of steps for RGB pixel pulsing

  def __init__(self, neoPixel=False, MCP3208=False):
    """ Initialize spin management
    """
    # Get the current time in seconds
    self._run_duration_s = 0
    self._start_s = time.time()

    # Initialize some variables
    self._ID = pf.GUID
    self._Tele = None
    self._MCP3208 = None
    self._Pix_enablePulse = False
    self.onboardLED = None
    self._NPx = None
    self._DS = None

    if MCP3208:
      # Initialize analog sensor driver
      from robotling_lib.driver import mcp3208
      dev = None if pf.ID == pf.ENV_ESP32_S2 else 1
      self._SPI = busio.SPIBus(rb.SPI_FRQ, rb.SCK, rb.SDI, rb.SDO, spidev=dev)
      self._MCP3208 = mcp3208.MCP3208(self._SPI, rb.CS_ADC)

    # RGB Pixel management
    if neoPixel:
      # Initialize Neopixel (connector)
      if pf.languageID == pf.LNG_MICROPYTHON:
        from robotling_lib.platform.esp32.neopixel import NeoPixel
      elif pf.languageID == pf.LNG_CIRCUITPYTHON:
        from robotling_lib.platform.circuitpython.neopixel import NeoPixel
      self._NPx = NeoPixel(rb.NEOPIX, 1)
      self._NPx.set((0,0,0), 0, True)
      s = "[{0:>12}] {1:35}".format("Neopixel", "ready")
      print(ansi.GREEN +s +ansi.BLACK)
    if rb.DS_CLOCK:
      # Initialize onboard RGB LED, if present
      from robotling_lib.driver.dotstar import DotStar
      self._stateDS = True
      self.dotStarPower = self._stateDS
      self._DS = DotStar(rb.DS_CLOCK, rb.DS_DATA, 1, brightness=0.5)
      self._DS[0] = 0
    if self._DS or self._NPx:
      # Initialize pulse management
      self._Pix_enablePulse = True
      self._Pix_iColor = 0
      self._Pix_RGB = bytearray([0]*3)
      self._Pix_curr = array.array("i", [0,0,0])
      self._Pix_step = array.array("i", [0,0,0])
      self._Pix_fact = 1.0
      self._Pix_pulse = False
      self.PixelRGB = 0

    # Initialize on-board (feather) hardware
    if rb.RED_LED:
      self.onboardLED = dio.DigitalOut(rb.RED_LED)

    # Initialize spin function-related variables
    self._spin_period_ms = 0
    self._spin_t_last_ms = 0
    self._spin_callback = None
    self._spinTracker = TimeTracker()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def memory(self):
    gc.collect()
    return (gc.mem_alloc(), gc.mem_free())

  @property
  def ID(self):
    return self._ID

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def powerDown(self):
    """ Record run time
    """
    if self._NPx:
      self._NPx.set((0,0,0), 0, True)
    if self._DS:
      self._DS[0] = 0
      self.dotStarPower = False
    self._run_duration_s = time.time() -self._start_s

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def dotStarPower(self):
    return self._stateDS

  @dotStarPower.setter
  def dotStarPower(self, state):
    if not rb.DS_POWER:
      return
    if state:
      Pin(rb.DS_POWER, Pin.OUT, None)
      Pin(rb.DS_POWER).value(False)
    else:
      Pin(rb.DS_POWER, Pin.IN, Pin.PULL_HOLD)
    Pin(rb.DS_CLOCK, Pin.OUT if state else Pin.IN)
    Pin(rb.DS_DATA, Pin.OUT if state else Pin.IN)
    time.sleep_ms(35)
    self._stateDS = state

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def updateStart(self):
    """ To be called at the beginning of the update function
    """
    self._spinTracker.reset()
    if self._MCP3208:
      self._MCP3208.update()
    if self._Pix_enablePulse:
      self._pulsePixel()

  def updateEnd(self):
    """ To be called at the end of the update function
    """
    if self._spin_callback:
      self._spin_callback()
    self._spinTracker.update()

  def spin_ms(self, dur_ms=0, period_ms=-1, callback=None):
    """ If not using a Timer to call `update()` regularly, calling `spin()`
        once per main loop and everywhere else instead of `time.sleep_ms()`
        is an alternative to keep the robotling board updated.
        e.g. "spin(period_ms=50, callback=myfunction)"" is setting it up,
             "spin(100)"" (~sleep for 100 ms) or "spin()" keeps it running.
    """
    if self._spin_period_ms > 0:
      p_ms = self._spin_period_ms
      p_us = p_ms *1000
      d_us = dur_ms *1000

      if dur_ms > 0 and dur_ms < (p_ms -APPROX_UPDATE_DUR_MS):
        time.sleep_ms(int(dur_ms))

      elif dur_ms >= (p_ms -APPROX_UPDATE_DUR_MS):
        # Sleep for given time while updating the board regularily; start by
        # sleeping for the remainder of the time to the next update ...
        t_us  = time.ticks_us()
        dt_ms = time.ticks_diff(time.ticks_ms(), self._spin_t_last_ms)
        if dt_ms > 0 and dt_ms < p_ms:
          time.sleep_ms(dt_ms)

        # Update
        self.update()
        self._spin_t_last_ms = time.ticks_ms()

        # Check if sleep time is left ...
        d_us = d_us -int(time.ticks_diff(time.ticks_us(), t_us))
        if d_us <= 0:
          return

        # ... and if so, pass the remaining time by updating at regular
        # intervals
        while time.ticks_diff(time.ticks_us(), t_us) < (d_us -p_us):
          time.sleep_us(p_us)
          self.update()

        # Remember time of last update
        self._spin_t_last_ms = time.ticks_ms()

      else:
        # No sleep duration given, thus just check if time is up and if so,
        # call update and remember time
        d_ms = time.ticks_diff(time.ticks_ms(), self._spin_t_last_ms)
        if d_ms > self._spin_period_ms:
          self.update()
          self._spin_t_last_ms = time.ticks_ms()

    elif period_ms > 0:
      # Set up spin parameters and return
      self._spin_period_ms = period_ms
      self._spin_callback = callback
      self._spinTracker.reset(period_ms)
      self._spin_t_last_ms = time.ticks_ms()

    else:
      # Spin parameters not setup, therefore just sleep
      time.sleep_ms(dur_ms)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def connectToWLAN(self):
    """ Connect to WLAN if not already connected
    """
    if pf.ID in [pf.ENV_ESP32_UPY, pf.ENV_ESP32_TINYPICO, pf.ENV_ESP32_S2]:
      import network
      from NETWORK import my_ssid, my_wp2_pwd
      if not network.WLAN(network.STA_IF).isconnected():
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
          print('Connecting to network...')
          sta_if.active(True)
          sta_if.connect(my_ssid, my_wp2_pwd)
          while not sta_if.isconnected():
            self.onboardLED.on()
            time.sleep(0.05)
            self.onboardLED.off()
            time.sleep(0.05)
          print("[{0:>12}] {1}".format("network", sta_if.ifconfig()))

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def printReport(self):
    """ Prints a report on memory usage and performance
    """
    self.printMemory(report=True)
    avg_ms = self._spinTracker.meanDuration_ms
    dur_ms = self._spinTracker.period_ms
    print("Performance: spin: {0:6.3f}ms @ {1:.1f}Hz ~{2:.0f}%"
          .format(avg_ms, 1000/dur_ms, avg_ms /dur_ms *100))

  def printMemory(self, do_collect=False, report=False):
    """ Prints just the information about memory usage
    """
    for i in range(2 if do_collect else 1):
      used, free = self.memory
      total = free +used
      used_p = used/total*100
      tot_kb = total/1024
      s = "Memory     : " if report else ""
      print("{0}{1:.0f}% of {2:.0f}kB heap RAM used.".format(s, used_p, tot_kb))
      if do_collect:
        gc.collect()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def PixelRGB(self):
    return self._Pix_RGB

  @PixelRGB.setter
  def PixelRGB(self, value):
    """ Set color of RGB LEDs ("Pixel") by assigning a RGB value or a color
        wheel index (and stop pulsing, if running)
    """
    try:
      rgb = bytearray([value[0], value[1], value[2]])
    except TypeError:
      rgb = getColorFromWheel(value)
    if self._NPx:
      self._NPx.set(rgb, 0, True)
    if self._DS:
      self._DS[0] = self._Pix_curr
      self._DS.show()
    self._Pix_pulse = False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def startPulsePixel(self, value):
    """ Set color of RGB LEDs and enable pulsing
    """
    iColPrev = self._Pix_iColor
    if self._Pix_enablePulse:
      try:
        rgb = bytearray([value[0], value[1], value[2]])
      except TypeError:
        rgb = getColorFromWheel(value)
        self._Pix_iColor = value

      if (rgb != self._Pix_RGB) or not(self._Pix_pulse):
        # New color and start pulsing
        c = self._Pix_curr
        s = self._Pix_step
        c[0] = rgb[0]
        s[0] = int(rgb[0] /self.HEARTBEAT_STEPS)
        c[1] = rgb[1]
        s[1] = int(rgb[1] /self.HEARTBEAT_STEPS)
        c[2] = rgb[2]
        s[2] = int(rgb[2] /self.HEARTBEAT_STEPS)
        self._Pix_RGB = rgb
        if self._NPx:
          self._NPx.set(rgb, 0, True)
        if self._DS:
          self._DS[0] = self._Pix_curr
          self._DS.show()
        self._Pix_pulse = True
        self._Pix_fact = 1.0
    return iColPrev

  def dimPixel(self, factor=1.0):
    self._Pix_fact = max(min(1, factor), 0)

  def _pulsePixel(self):
    """ Update pulsing, if enabled
    """
    if self._Pix_pulse:
      rgb = self._Pix_RGB
      for i in range(3):
        self._Pix_curr[i] += self._Pix_step[i]
        if self._Pix_curr[i] > (rgb[i] -self._Pix_step[i]):
          self._Pix_step[i] *= -1
        if self._Pix_curr[i] < abs(self._Pix_step[i]):
          self._Pix_step[i] = abs(self._Pix_step[i])
        if self._Pix_fact < 1.0:
          self._Pix_curr[i] = int(self._Pix_curr[i] *self._Pix_fact)
        self._Pix_curr[i] = min(self._Pix_curr[i], 255)
      if self._NPx:
        self._NPx.set(self._Pix_curr, 0, True)
      if self._DS:
        self._DS[0] = self._Pix_curr
        self._DS.show()

# ----------------------------------------------------------------------------
