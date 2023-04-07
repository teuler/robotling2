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
import utime
from machine import Pin, I2C, ADC
import micropython
              
from robotling_lib.platform.rp2 import board_rp2 as board
from vl53l0x import setup_tofl_device, TBOOT
import rbl2_gui
import rbl2_config as cfg
import rbl2_global as glb
import rbl2_gait as gait

# pylint: disable=bad-whitespace
__version__  = "0.1.0.0"

# Global variables to communicate with task on core 1
# (Do not access other than via the `RobotBase` instance!!)
g_state_gait = glb.STATE_NONE
g_state      = glb.STATE_NONE
g_cmd        = glb.CMD_NONE
g_counter    = 0
g_dist_evo   = None
g_move_dir   = 0.
g_move_vel   = 2
g_do_exit    = False
g_led        = Pin(board.D11, Pin.OUT)
    
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class Robot(object):
  """Robot representation"""

  def __init__(self, core=1, use_gui=True, verbose=False):
    global g_state
    global g_dist_tof
    global tofl0, tofl1, tofl2
    global g_gui
    global g_gait

    g_gui = rbl2_gui.GUI()
    g_gait = gait.Gait()
    # Initializing ...
    g_state = glb.STATE_NONE
    self._verbose = verbose
    self._core = core
    self._spin_period_ms = 0
    self._spin_t_last_ms = 0
    self._do_autoupdate_gui = False
    self._no_servos = False

    # Initializing some hardware
    self._pinVBUSPresent = Pin(board.VBUS, Pin.IN)
    self._pinPower_V = ADC(Pin(board.BAT))

    # Initialize picodisplay, if any
    if g_gui:
      g_gui.clear()
      g_gui.LED.startPulse(150)
      g_gui.on(True)
      g_gui.show_version()
      g_gui.show_general_info("n/a")

    # Initialize devices
    if "VL53L0x" in cfg.DEVICES:
        device_1_xshut = Pin(cfg.TOFL_SHUT_1, Pin.OUT)
        device_2_xshut = Pin(cfg.TOFL_SHUT_2, Pin.OUT)
        device_1_xshut.value(1)
        device_2_xshut.value(1)
        utime.sleep_us (TBOOT)
        i2c = I2C(id=cfg.TOFL_I2C, sda=Pin(cfg.TOFL_SDA), scl=Pin(cfg.TOFL_SCL))

        addresses =i2c.scan()
        if (not (0x31 in addresses)):
#            print("Setting up device 0")
            device_1_xshut.value(0)
            device_2_xshut.value(0)
            tofl0 = setup_tofl_device(i2c, 40000, 12, 8)
            tofl0.set_address(0x31)
        else:
#            print("Reconnect device 0")
            device_1_xshut.value(0)
            device_2_xshut.value(0)
            tofl0 = setup_tofl_device(i2c, 40000, 12, 8, 0x31)

        if (not (0x33 in addresses)):
#            print("Setting up device 1")
            device_1_xshut.value(1)
            device_2_xshut.value(0)
            utime.sleep_us(TBOOT)
            tofl1 = setup_tofl_device(i2c, 40000, 12, 8)
            tofl1.set_address(0x33)
        else:
#            print("Reconnect device 1")
            device_1_xshut.value(1)
            device_2_xshut.value(0)
            utime.sleep_us(TBOOT)
            tofl1 = setup_tofl_device(i2c, 40000, 12, 8, 0x33)

        if (0x29 in addresses):
#            print("Now setting up device 2")
            # Re-enable device 2 - on the same bus
            device_1_xshut.value(1)
            device_2_xshut.value(1)
            utime.sleep_us(TBOOT)
            tofl2 = setup_tofl_device(i2c, 40000, 12, 8)
        else:
            print("!!!!Fehler!!!")
            
        g_dist_tof = True

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
    if g_gui:
      g_gui.deinit()
      g_gui.LED.RGB = (60,0,0)
    if g_dist_tof:
      tofl0.set_address(0x29)
      tofl1.set_address(0x29)
    if g_state is not glb.STATE_OFF:
      self.power_down()
      counter = 0
      while g_state is not glb.STATE_OFF:
        assert counter > 1000, "Locked in `RobotBase.deinit`"
        counter += 1
        self.sleep_ms(50)


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
  def distances_mm(self):
    """ Returns the distances (in [mm]) as an array. The lengths of the array
        depends on the sensor: e.g. the vl53l0x reports 1 value, 3 times.
    """
    if g_dist_tof:
        _d = array.array('i', (0 for _ in range(3)))
        _d[0] = tofl2.ping()
        _d[1] = tofl0.ping()
        _d[2] = tofl1.ping()
#        _d = [150, 150, 150]
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
    """
    return self._pinPower_V.read_u16()*3/65536*3.3

  # GUI-related properties
  @property
  def autoupdate_gui(self):
    """ Endable/disable autoupdate of GUI during `sleep_ms`
    """
    return self._do_autoupdate_gui
  @autoupdate_gui.setter
  def autoupdate_gui(self, val :bool):
    self._do_autoupdate_gui = val

  @property
  def is_pressed_A(self):
    return g_gui.display.is_pressed(g_gui.display.BUTTON_A) if g_gui else False

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
      if g_dist_tof:
        g_gui.show_distance_tof(self.distances_mm)

  def show_message(self, msg):
    """ Show a message on the display
    """
    if g_gui:
      g_gui.show_msg(msg)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def move_forward(self, wait_for_idle=False):
    """ Move straight forward using current gait and velocity.
        If `wait_for_idle` is True, then trigger action only when idle.
    """
    global g_cmd, g_move_dir
    if not wait_for_idle or g_state_gait == glb.STATE_IDLE:
      g_move_dir = 0.
      if not self._no_servos:
        g_cmd = glb.CMD_MOVE

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
    glb.toLog("Request hardware thread power down ...")
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

    if g_state == glb.STATE_OFF:
      return
    if g_state is not glb.STATE_POWERING_DOWN:
      g_led.value(1)

      # Handle new command, if any ...
      if g_cmd is not glb.CMD_NONE:

        if g_cmd == glb.CMD_MOVE:
          g_gait.direction = g_move_dir
          g_gait.walk()
          g_state = glb.STATE_WALKING if g_move_dir == 0 else glb.STATE_TURNING

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
              g_gait.walk()
              if g_move_dir == 0:
                g_state = glb.STATE_WALKING
              else:
                g_state = glb.STATE_TURNING

            if g_cmd == glb.CMD_STOP:
              g_gait.stop()
              g_state = glb.STATE_STOPPING

            if g_cmd == glb.CMD_POWER_DOWN:
              # Stop and power down ...
              g_gait.stop()
              g_do_exit = True

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
if __name__ == "__main__":
# Initialize robot
  micropython.mem_info()
  Robot = Robot(core=cfg.HW_CORE)
  Robot.autoupdate_gui = True
  micropython.mem_info()

  print("Press `A` for sensors only ...")
  trials = 80
  only_sensors = False 
  while trials > 0:
    if Robot.is_pressed_A:
      only_sensors = True
      break
    trials -= 1
    time.sleep_ms(25)
  if only_sensors:
    Robot.show_message("sensors-only")
    print ("Sensors  Only")
    Robot.no_servos(only_sensors)
  try:
    while not Robot.state == glb.STATE_OFF:
      dL, dC, dR = Robot.distances_mm

      if not only_sensors:
        objL = (dL < 80) or (dC < 80)
        objR = (dR < 80) or (dC < 80)
        clfL = (dL > 200) or (dC > 200)
        clfR = (dR > 200) or (dC > 200)
        free = not objL and not objR and not clfL and not clfR

        if free:
          if Robot.state is not glb.STATE_WALKING:
            Robot.move_forward()
            Robot.show_message("-")
        else:
          Robot.stop()
          while Robot.state is not glb.STATE_IDLE: Robot.sleep_ms(25)

          if clfL or clfR:
            if clfL and not clfR:
              Robot.turn(+1)
              Robot.show_message("Cliff_L__")
            elif not clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff___R")
            elif clfL and clfR:
              Robot.turn(-1)
              Robot.show_message("Cliff__C_")
            Robot.sleep_ms(4000)

          elif objL or objR:
            if objL and not objR:
              Robot.turn(+1)
              Robot.show_message("Objct_L__")
            elif not objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct___R")
            elif objL and objR:
              Robot.turn(-1)
              Robot.show_message("Objct__C_")
            Robot.sleep_ms(2000)

      # Sleep for a while and, if running only on one core, make sure that
      # the robot's hardware is updated
      Robot.sleep_ms(50)

  except KeyboardInterrupt:
    # Clean up
    Robot.deinit()

# ----------------------------------------------------------------------------
 
