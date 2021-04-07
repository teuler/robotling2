# ----------------------------------------------------------------------------
# rbl2_robot.py
#
# Representation of the robot
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-04-03, v1.0
# ----------------------------------------------------------------------------
import time
import array
import _thread
from machine import Pin
import rbl2_config as cfg
import rbl2_global as glb
import rbl2_gait as gait
import rbl2_gui
from robotling_lib.platform.rp2 import board_rp2 as board

# pylint: disable=bad-whitespace
__version__  = "0.1.0.0"

# Global variables to communicate with task on core 1
g_state_gait = glb.STATE_NONE
g_state      = glb.STATE_NONE
g_cmd        = glb.CMD_NONE
g_move_dir   = 0.
g_gui        = rbl2_gui.GUI()
# ...
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class RobotBase(object):
  """Robot representation"""

  def __init__(self, core=1, use_gui=True, verbose=False):
    global g_state, g_state_gait
    global g_gui

    # Initializing ...
    g_state = glb.STATE_NONE
    self._verbose = verbose
    self._core = core
    self._spin_period_ms = 0
    self._spin_t_last_ms = 0

    # Initialize picodisplay, if any
    if g_gui:
      g_gui.clear()
      g_gui.LED.startPulse(150)
      g_gui.on(True)
      g_gui.show_version()
      g_gui.show_info("n/a")

    # Depending on `core`, the thread that updates the hardware either runs
    # on the second core (`core` == 1) or on the same core as the main program
    # (`core` == 0). In the latter case, the classes `sleep_ms()` function
    # needs to be used and called frequencly to keep the hardware updated.
    if self._core == 1:
      # Starting hardware thread on core 1 and wait until it is ready
      self._Task = _thread.start_new_thread(self._task_core1, ())
      glb.toLog("Hardware thread on core 1 starting ...")
      while not g_state_gait == glb.STATE_IDLE:
        time.sleep_ms(50)
      glb.toLog("Hardware thread ready.")
    else:
      # Do not use core 1 for hardware thread; instead the main loop has to
      # call `sleep_ms()` frequently.
      self._prepare()
      self.sleep_ms(period_ms=cfg.MIN_UPDATE_MS, callback=self._task_core0)
      glb.toLog("Hardware co-uses core 0.")

    g_state = glb.STATE_IDLE

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def deinit(self):
    global g_state, g_gui
    if g_state is not glb.STATE_OFF:
      self.power_down()
      counter = 0
      while g_state is not glb.STATE_OFF:
        assert counter < 200, "Locked in `RobotBase.deinit`"
        time.sleep_ms(50)
    if g_gui:
      g_gui.deinit()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def state(self):
    global g_state
    return g_state

  @property
  def direction(self):
    global g_move_dir
    return g_move_dir

  @property
  def GUI(self):
    global g_gui
    return g_gui

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def move_forward(self, wait_for_idle=False):
    """ Move straight forward using current gait and velocity.
        If `wait_for_idle` is True, then trigger action only when idle.
    """
    global g_cmd, g_move_dir, g_state_gait
    if not wait_for_idle or g_state_gait == glb.STATE_IDLE:
      g_move_dir = 0.
      g_cmd = glb.CMD_MOVE

  def turn(self, dir, wait_for_idle=False):
    """ Turn using current gait and velocity; making with `dir` < 0 a left and
        `dir` > 0 a right turn. The size of `dir` (1 >= |`dir`| > 0) giving
        the turning strength (e.g. 1.=turn in place, 0.2=walk in a shallow
        curve). If `wait_for_idle` is True, then trigger action only when idle.
    """
    global g_cmd, g_move_dir, g_state_gait
    if not wait_for_idle or g_state_gait == glb.STATE_IDLE:
      g_move_dir = max(min(dir, 1.0), -1.0)
      g_cmd = glb.CMD_MOVE

  def stop(self):
    """ Stop if walking
    """
    global g_cmd, g_state_gait
    if g_state_gait in [glb.STATE_WALKING, glb.STATE_TURNING]:
      g_cmd = glb.CMD_STOP

  def power_down(self):
    """ Power down and end task
    """
    global g_cmd
    glb.toLog("Request hardware thread power down ...")
    g_move_dir = 0.
    g_cmd = glb.CMD_POWER_DOWN

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _prepare(self):
    global g_state_gait

    # Initialize hardware
    self._g = gait.Gait()
    self._g.velocity = 2
    self._do_exit = False
    g_state_gait = glb.STATE_IDLE

    # Initialize activity LED
    self._LED = Pin(board.D11, Pin.OUT)

  def _task_core0(self):
    global g_state_gait, g_state
    global g_cmd, g_move_dir
    global g_gui

    if g_state == glb.STATE_OFF:
      return
    if g_state is not glb.STATE_POWERING_DOWN:
      self._LED.value(1)

      # Handle new command, if any ...
      if g_cmd is not glb.CMD_NONE:

        if g_cmd == glb.CMD_MOVE:
          self._g.direction = g_move_dir
          self._g.walk()
          g_state = glb.STATE_WALKING if g_move_dir == 0 else glb.STATE_TURNING

        if g_cmd == glb.CMD_STOP:
          self._g.stop()
          g_state = glb.STATE_STOPPING

        if g_cmd == glb.CMD_POWER_DOWN:
          # Stop and power down ...
          self._g.stop()
          self._do_exit = True

        g_cmd = glb.CMD_NONE

      # Wait for transitions to update state accordingly ...
      if g_state == glb.STATE_STOPPING and g_state_gait == glb.STATE_IDLE:
        g_state = glb.STATE_IDLE
      if g_state == glb.STATE_IDLE and self._do_exit:
        g_state = glb.STATE_POWERING_DOWN

      # Spin everyone who needs spinning
      self._g._spin()
      g_state_gait = self._g.state
      g_gui.spin()
      self._LED.value(0)

    else:
      # Finalize ...
      self._g.deinit()
      self._LED.value(0)
      g_state = glb.STATE_OFF

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

        # Remember time of last update
        self._spin_t_last_ms = time.ticks_ms()

      else:
        # No sleep duration given, thus just check if time is up and if so,
        # call update and remember time
        d_ms = time.ticks_diff(time.ticks_ms(), self._spin_t_last_ms)
        if d_ms > self._spin_period_ms:
          self._spin_callback()
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
  @staticmethod
  def _task_core1():
    global g_state_gait, g_state
    global g_cmd, g_move_dir
    global g_gui

    # Initialize hardware
    g = gait.Gait()
    g.velocity = 2

    # Initialize activity LED
    LED = Pin(board.D11, Pin.OUT)

    # Loop
    do_exit = False
    try:
      try:
        g_state_gait = glb.STATE_IDLE

        # Main loop ...
        while g_state is not glb.STATE_POWERING_DOWN:
          LED.value(1)

          # Handle new command, if any ...
          if g_cmd is not glb.CMD_NONE:

            if g_cmd == glb.CMD_MOVE:
              g.direction = g_move_dir
              g.walk()
              g_state = glb.STATE_WALKING if g_move_dir == 0 else glb.STATE_TURNING

            if g_cmd == glb.CMD_STOP:
              g.stop()
              g_state = glb.STATE_STOPPING

            if g_cmd == glb.CMD_POWER_DOWN:
              # Stop and power down ...
              g.stop()
              do_exit = True

            g_cmd = glb.CMD_NONE

          # Wait for transitions to update state accordingly ...
          if g_state == glb.STATE_STOPPING and g_state_gait == glb.STATE_IDLE:
            g_state = glb.STATE_IDLE
          if g_state == glb.STATE_IDLE and do_exit:
            g_state = glb.STATE_POWERING_DOWN

          # Spin everyone who needs spinning
          g._spin()
          g_state_gait = g.state
          g_gui.spin()
          LED.value(0)

          # Wait for a little while
          time.sleep_ms(25)

      except KeyboardInterrupt:
        pass

    finally:
      g.deinit()
      LED.value(0)
      glb.toLog("Hardware thread ended.")
      g_state = glb.STATE_OFF

# ----------------------------------------------------------------------------
