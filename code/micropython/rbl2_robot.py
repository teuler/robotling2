# ----------------------------------------------------------------------------
# rbl2_robot.py
#
# Representation of the robot
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-04-03, v1.0
# 2022-02-12, v1.1
# 2022-04-08, v1.2, small fixes for MicroPython 1.18
# ----------------------------------------------------------------------------
import time
import array
from machine import Pin, ADC
import rbl2_config as cfg
import rbl2_global as glb
import rbl2_gait as gait
import rbl2_gui
from robotling_lib.platform.rp2 import board_rp2 as board
from robotling_lib.misc.helpers import timed_function

# pylint: disable=bad-whitespace
__version__  = "0.1.3.0"

# Global variables to communicate with task on core 1
# (Do not access other than via the `RobotBase` instance!!)
g_state_gait = glb.STATE_NONE
g_state      = glb.STATE_NONE
g_cmd        = glb.CMD_NONE
g_counter    = 0
g_gui        = None
g_dist_evo   = None
g_dist_tof   = None
g_dist_type  = cfg.STY_NONE
g_gait       = None
g_move_dir   = 0.
g_move_vel   = 2
g_move_rev   = False
g_do_exit    = False
g_led        = Pin(board.D11, Pin.OUT)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class Robot(object):
  """Robot representation"""

  def __init__(self, core=1, use_gui=True, verbose=False, no_servos=False):
    global g_state, g_gui, g_gait
    global g_dist_evo, g_dist_tof, g_dist_type

    # Initializing ...
    glb.toLog("Initializing ...")
    g_state = glb.STATE_NONE
    self._verbose = verbose
    self._core = core
    self._spin_period_ms = 0
    self._spin_t_last_ms = 0
    self._do_autoupdate_gui = False
    self._no_servos = False
    self._user_abort = False

    # Initializing some hardware
    self._pinVBUSPresent = Pin(board.VBUS, Pin.IN)
    self._pinPower_V = ADC(Pin(board.BAT))

    # Initialize display, if any
    if "display" in cfg.DEVICES:
      g_gui = rbl2_gui.GUI()
      g_gui.clear()
      g_gui.LED.startPulse(150)
      g_gui.on(True)
      g_gui.show_version()
      g_gui.show_general_info("n/a")

    # Initialize servos/gait
    # (Has to happen after initializing (Pimoroni) display to re-claim pins)
    g_gait = gait.Gait()

    # Initialize devices
    if "evo_mini" in cfg.DEVICES:
      # 4-channel TeraRanger Evo Mini from Terabee
      from robotling_lib.sensors.teraranger_evomini import TeraRangerEvoMini
      g_dist_evo = TeraRangerEvoMini(
          cfg.EVOMINI_UART,
          tx=Pin(cfg.EVOMINI_TX), rx=Pin(cfg.EVOMINI_RX)
        )
      time.sleep_ms(1000)
      g_dist_type = cfg.STY_EVOMINI

    if "tof_pwm" in cfg.DEVICES:
      # 3x 1-channel Time-of-flight sensors w/ PWM output from Pololu
      g_dist_type = cfg.STY_TOF
      g_dist_tof = []
      if cfg.TOFPWM_USE_PIO:
        from robotling_lib.sensors.pololu_tof_ranging_pio import PololuTOFRangingSensor
        for i, p in enumerate(cfg.TOFPWM_PINS):
          g_dist_tof.append(PololuTOFRangingSensor(p, cfg.TOFPWM_PIOS[i]))
      else:
        from robotling_lib.sensors.pololu_tof_ranging import PololuTOFRangingSensor
        for p in cfg.TOFPWM_PINS:
          g_dist_tof.append(PololuTOFRangingSensor(p))

    # Depending on `core`, the thread that updates the hardware either runs
    # on the second core (`core` == 1) or on the same core as the main program
    # (`core` == 0). In the latter case, the classes `sleep_ms()` function
    # needs to be used and called frequencly to keep the hardware updated.
    if self._core == 1:
      # Starting hardware thread on core 1 and wait until it is ready
      import _thread
      self._Task = _thread.start_new_thread(self._task_core1, ())
      glb.toLog("Hardware thread on core 1 starting ...")
      while not g_state_gait == glb.STATE_IDLE:
        time.sleep_ms(50)
      glb.toLog("Hardware thread ready.")
    else:
      # Do not use core 1 for hardware thread; instead the main loop has to
      # call `sleep_ms()` frequently. Here, prime that sleep function ...
      self.sleep_ms(period_ms=cfg.MIN_UPDATE_MS, callback=self._task_core0)
      glb.toLog("Hardware co-uses core 0.")

    g_state = glb.STATE_IDLE

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def deinit(self):
    global g_state, g_gui

    glb.toLog("Deinit sensors ...")
    if "tof_pwm" in cfg.DEVICES:
      for sens in g_dist_tof:
        sens.deinit()

    if g_state is not glb.STATE_OFF:
      glb.toLog("Powering down ...")
      self.power_down()
      while g_state is not glb.STATE_OFF:
        self.sleep_ms(25)

    glb.toLog("Turning servos off ...")
    self.turn_servos_off()
    if g_gui:
      glb.toLog("Clearing display and LED ...")
      g_gui.deinit()
      g_gui.LED.RGB = (60,0,0)

    glb.toLog("Done.")

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def state(self):
    """ Returns `state` as a constant `STATE_xxx` (defined in `rbl2_global.py`)
    """
    return g_state

  @property
  def direction(self):
    """ Returns current movement direction (see `turn()` for details)
    """
    return g_move_dir

  @property
  def distance_sensor_type(self):
    return g_dist_type

  #@timed_function
  @property
  def distances_mm(self):
    """ Returns the distances (in [mm]) as an array. The lengths of the array
        depends on the sensor: e.g. the TeraRanger Evo mini reports 4 values.
    """
    if g_dist_evo:
      _d = array.array("i", g_dist_evo.distances)
      for i in range(len(_d)):
        if _d[i] == g_dist_evo.TERA_DIST_POS_INF or _d[i] > cfg.EVOMINI_MAX_MM:
          _d[i] = cfg.EVOMINI_MAX_MM
        elif _d[i] == g_dist_evo.TERA_DIST_NEG_INF:
          _d[i] = cfg.EVOMINI_MIN_MM
        elif _d[i] == g_dist_evo.TERA_DIST_INVALID:
          _d[i] = -1
      self._last_dist = _d
      return _d
    elif g_dist_tof:
      _d = array.array("i", [0]*len(g_dist_tof))
      for i, tof in enumerate(g_dist_tof):
        _d[i] = int(tof.range_cm *10)
      self._last_dist = _d
      return _d
    else:
      return []

  @property
  def is_connected_via_usb(self):
    """ Returns True if connected via USB cable (and VSYS is present)
    """
    return self._pinVBUSPresent.value()

  @property
  def power_V(self):
    """ Returns the input voltage that powers the microcontroller
        TODO: Fix reported voltage (unclear why not correct)
    """
    return self._pinPower_V.read_u16() *3 *3.3 /65535

  @property
  def exit_requested(self):
    """ Returns True if the `X` button was pressed during `sleep_ms()`
    """
    return self._user_abort

  # GUI-related properties
  @property
  def autoupdate_gui(self):
    """ Endable/disable autoupdate of GUI during `sleep_ms`
    """
    return self._do_autoupdate_gui
  @autoupdate_gui.setter
  def autoupdate_gui(self, val :bool):
    self._do_autoupdate_gui = val if g_gui else False

  @property
  def is_pressed_A(self):
    return g_gui._BtnA.is_pressed if g_gui else False

  @property
  def is_pressed_B(self):
    return g_gui._BtnB.is_pressed if g_gui else False

  @property
  def is_pressed_X(self):
    return g_gui._BtnX.is_pressed if g_gui else False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def update_display(self):
    """ If display is connected, show important status information there
    """
    if g_gui:
      vbus = self._pinVBUSPresent.value()
      pw_V = self.power_V
      g_gui.show_general_info(glb.STATE_STRS[g_state],
          "{0:.1f}".format(g_move_dir) if g_state is glb.STATE_TURNING else "",
          vbus, pw_V
        )
      if g_dist_evo:
        g_gui.show_distance_evo(self._last_dist)
      if g_dist_tof:
        g_gui.show_distance_tof(self._last_dist)

  def show_message(self, msg):
    """ Show a message on the display
    """
    if g_gui:
      g_gui.show_msg(msg)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def move_forward(self, wait_for_idle=False, reverse=False):
    """ Move straight forward using current gait and velocity.
        If `wait_for_idle` is True, then trigger action only when idle.
    """
    global g_cmd, g_move_dir, g_move_rev
    if not wait_for_idle or g_state_gait == glb.STATE_IDLE:
      g_move_dir = 0.
      g_move_rev = reverse
      if not self._no_servos:
        g_cmd = glb.CMD_MOVE

  def move_backward(self, wait_for_idle=False):
    self.move_forward(wait_for_idle, True)

  def turn(self, dir, wait_for_idle=False):
    """ Turn using current gait and velocity; making with `dir` < 0 a left and
        `dir` > 0 a right turn. The size of `dir` (1 >= |`dir`| > 0) giving
        the turning strength (e.g. 1.=turn in place, 0.2=walk in a shallow
        curve). If `wait_for_idle` is True, then trigger action only when idle.
    """
    global g_cmd, g_move_dir
    if not wait_for_idle or g_state_gait == glb.STATE_IDLE:
      g_move_dir = max(min(dir, 1.0), -1.0)
      if not self._no_servos:
        g_cmd = glb.CMD_MOVE

  def stop(self):
    """ Stop if walking
    """
    global g_cmd
    if g_state_gait in [glb.STATE_WALKING, glb.STATE_TURNING]:
      g_cmd = glb.CMD_STOP

  def turn_servos_off(self):
    g_gait._SM.turn_all_off()

  def no_servos(self, val):
    self._no_servos = val

  def power_down(self):
    """ Power down and end task
    """
    global g_cmd, g_move_dir
    g_move_dir = 0.
    g_cmd = glb.CMD_POWER_DOWN

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sleep_ms(self, dur_ms=0, period_ms=-1, callback=None):
    """ This function is an alternative to `time.sleep_ms()`; it sleeps but
        also  keep the robot's hardware updated.
        e.g. "sleep_ms(period_ms=50, callback=myfunction)"" is setting it up,
             "sleep_ms(100)"" (~sleep for 100 ms) or "sleep_ms()" keeps it
             running.
    """
    if self._spin_period_ms > 0:
      p_ms = self._spin_period_ms
      p_us = p_ms *1000
      d_us = dur_ms *1000

      if dur_ms > 0 and dur_ms < (p_ms -cfg.APPROX_SPIN_MS):
        time.sleep_ms(int(dur_ms))

      elif dur_ms >= (p_ms -cfg.APPROX_SPIN_MS):
        # Sleep for given time while updating the board regularily; start by
        # sleeping for the remainder of the time to the next update ...
        t_us  = time.ticks_us()
        dt_ms = time.ticks_diff(time.ticks_ms(), self._spin_t_last_ms)
        if dt_ms > 0 and dt_ms < p_ms:
          time.sleep_ms(dt_ms)

        # Update
        self._spin_callback()
        if self._do_autoupdate_gui:
          self.update_display()
        if self.is_pressed_X:
          self._user_abort = True
          return
        self._spin_t_last_ms = time.ticks_ms()

        # Check if sleep time is left ...
        d_us = d_us -int(time.ticks_diff(time.ticks_us(), t_us))
        if d_us <= 0:
          return

        # ... and if so, pass the remaining time by updating at regular
        # intervals
        while time.ticks_diff(time.ticks_us(), t_us) < (d_us -p_us):
          time.sleep_us(p_us)
          self._spin_callback()
          if self._do_autoupdate_gui:
            self.update_display()
          if self.is_pressed_X:
            self._user_abort = True
            return

        # Remember time of last update
        self._spin_t_last_ms = time.ticks_ms()

      else:
        # No sleep duration given, thus just check if time is up and if so,
        # call update and remember time
        d_ms = time.ticks_diff(time.ticks_ms(), self._spin_t_last_ms)
        if d_ms > self._spin_period_ms:
          self._spin_callback()
          if self._do_autoupdate_gui:
            self.update_display()
          self._spin_t_last_ms = time.ticks_ms()

    elif period_ms > 0:
      # Set up spin parameters and return
      self._spin_period_ms = period_ms
      self._spin_callback = callback
      self._spin_t_last_ms = time.ticks_ms()
    else:
      # Spin parameters not setup, therefore just sleep
      time.sleep_ms(dur_ms)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _task_core0(self):
    """ This is the core 0-version of the routine that keeps the hardware
        updated and responds to commands (e.g. move, turn).
        - It is called by `sleep_ms()`.
        - It uses only global variables for external objects to stay
          compatible with the core-1 version below.
    """
    global g_state_gait, g_state, g_counter
    global g_cmd, g_do_exit
    global g_move_dir, g_move_rev
    global g_dist_evo, g_led, g_gui

    if g_state == glb.STATE_OFF:
      return
    if g_state is not glb.STATE_POWERING_DOWN:
      g_led.value(1)

      # Handle new command, if any ...
      if g_cmd is not glb.CMD_NONE:

        if g_cmd == glb.CMD_MOVE:
          g_gait.direction = g_move_dir
          g_gait.reverse = g_move_rev
          g_gait.walk()
          if abs(g_move_dir) < 0.01:
            g_state = glb.STATE_WALKING if not g_move_rev else glb.STATE_REVERSING
          else:
            g_state = glb.STATE_TURNING

        if g_cmd in [glb.CMD_STOP, glb.CMD_POWER_DOWN]:
          # Stop or power down ...
          g_gait.stop()
          g_state = glb.STATE_STOPPING
          g_do_exit = g_cmd == glb.CMD_POWER_DOWN

        g_cmd = glb.CMD_NONE

      # Wait for transitions to update state accordingly ...
      if g_state == glb.STATE_STOPPING and g_state_gait == glb.STATE_IDLE:
        g_state = glb.STATE_IDLE
      if g_state == glb.STATE_IDLE and g_do_exit:
        g_state = glb.STATE_POWERING_DOWN

      # Spin everyone who needs spinning
      g_gait.spin()
      g_state_gait = g_gait.state
      if g_dist_evo:
        g_dist_evo.update(raw=True)
      if g_gui:
        g_gui.spin()
      g_counter += 1
      g_led.value(0)

    else:
      # Finalize ...
      g_gait.deinit()
      g_led.value(0)
      g_state = glb.STATE_OFF

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @staticmethod
  def _task_core1():
    """ This is the core 1-version of the routine that keeps the hardware
        updated and responds to commands (e.g. move, turn).
        - It runs independently on core 1; in parallel to the main program on
          core 0.
        - It communicates via global variables.
    """
    global g_state_gait, g_state, g_counter
    global g_cmd, g_do_exit
    global g_move_dir, g_move_rev
    global g_dist_evo, g_led, g_gui

    # Loop
    g_do_exit = False
    try:
      try:
        g_state_gait = glb.STATE_IDLE

        # Main loop ...
        while g_state is not glb.STATE_POWERING_DOWN:
          g_led.value(1)

          # Handle new command, if any ...
          if g_cmd is not glb.CMD_NONE:

            if g_cmd == glb.CMD_MOVE:
              g_gait.direction = g_move_dir
              g_gait.reverse = g_move_rev
              g_gait.walk()
              if abs(g_move_dir) < 0.01:
                g_state = glb.STATE_WALKING if not g_move_rev else glb.STATE_REVERSING
              else:
                g_state = glb.STATE_TURNING

            if g_cmd in [glb.CMD_STOP, glb.CMD_POWER_DOWN]:
              # Stop or power down ...
              g_gait.stop()
              g_state = glb.STATE_STOPPING
              g_do_exit = g_cmd == glb.CMD_POWER_DOWN

            g_cmd = glb.CMD_NONE

          # Wait for transitions to update state accordingly ...
          if g_state == glb.STATE_STOPPING and g_state_gait == glb.STATE_IDLE:
            g_state = glb.STATE_IDLE
          if g_state == glb.STATE_IDLE and g_do_exit:
            g_state = glb.STATE_POWERING_DOWN

          # Spin everyone who needs spinning
          g_gait.spin()
          g_state_gait = g_gait.state
          if g_dist_evo:
            g_dist_evo.update(raw=False)
          if g_gui:
            g_gui.spin()
          g_counter += 1
          g_led.value(0)

          # Wait for a little while
          time.sleep_ms(25)

      except KeyboardInterrupt:
        pass

    finally:
      g_gait.deinit()
      g_led.value(0)
      glb.toLog("Hardware thread ended.")
      g_state = glb.STATE_OFF

# ----------------------------------------------------------------------------
