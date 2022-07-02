# ----------------------------------------------------------------------------
# servo_manager.py
# Class to manage and control a number of servos
#
# The MIT License (MIT)
# Copyright (c) 2020-2022 Thomas Euler
# 2020-01-03, v1
# 2020-08-02, v1.1 ulab
# 2020-10-31, v1.2, use `languageID` instead of `ID`
# 2021-02-14, v1.3, small improvements towards more performance
# 2021-02-28, v1.4, compatibility w/ rp2, no `ulab` for space reasons
# 2022-01-04, v1.5, Nano RP2040 Connect added, simplified (only linear)
# 2022-05-05, v1.6, Calibration code added
# 2022-05-08, v1.7, TRJ_LINEAR=Normal, TRJ_SINE=slow start and end move
# 2022-06-11, v1.8, Allow setting last position after power-off
# 2022-06-26, v1.8, Added option not to use `ulab`
# ----------------------------------------------------------------------------
import gc
import time
import array
from machine import Timer
from robotling_lib.misc.helpers import timed_function
from robotling_lib.platform.platform import platform as pf
import robotling_lib.misc.ansi_color as ansi
try:
  from ulab import numpy as np
  ULAB = True
except ImportError:
  import math as np
  ULAB = False

# pylint: disable=bad-whitespace
__version__        = "0.1.8.0"
RATE_MS            = const(10)  # 5=hangs, 15...20=ok, 25=not continues
HARDWARE_TIMER     = const(0)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class ServoManager(object):
  """Class to manage and control a number of servos"""
  # pylint: disable=bad-whitespace
  TYPE_NONE       = const(0)
  TYPE_HORIZONTAL = const(1)
  TYPE_VERTICAL   = const(2)
  TYPE_SENSOR     = const(3)

  TRJ_LINEAR      = const(0)
  TRJ_SINE        = const(1)
  # pylint: enable=bad-whitespace

  def __init__(self, n, verbose=False):
    """ Initialises the management structures
    """
    self._isVerbose = verbose
    self._nChan = max(1, n)
    self._Servos = [None]*n                               # Servo objects
    self._servo_type = bytearray([TYPE_NONE]*n)           # Servo type
    self._servo_number = bytearray([255]*n)               # Servo number
    self._servoPos = array.array("f", [0]*n)              # Servo pos [us]
    self._SIDList = bytearray([255]*n)                    # Servos to move next
    self._targetPosList = array.array("H", [0]*n)         # Target pos [us]
    self._currPosList = array.array("f", [-1]*n)          # Current pos [us]
    self._stepSizeList = array.array("f", [0]*n)          # .. step sizes [us]
    self._nToMove = 0                                     # # of servos to move
    self._dt_ms = 0                                       # Time period [ms]
    self._nSteps = 0                                      # countdown of steps to move
    self._trajNormList = array.array("f", [0]*n)          # Sensor norm factor (TRJ_SINE)
    self._iStep = 0                                       # Current step
    self._nStTotal = 0                                    # total # of steps
    self._mm18 = None
    self._isMoving = False
    self._isFirstMove = True
    self._Timer = Timer() if pf.isRP2 else Timer(HARDWARE_TIMER)

  def add_servo(self, i, servoObj, pos=0):
    """ Add at the entry `i` of the servo list the servo object, which has to
        define the following functions:
        - `write_us(t_us)`
        - `angle_in_us(value=None)`
        - `off()`
        - `deinit()`
    """
    if i in range(self._nChan):
      self._Servos[i] = servoObj
      self._servoPos[i] = servoObj.angle_in_us()
      self._servo_number[i] = i
      if self._isVerbose:
        print("Add servo #{0:-2.0f}, at {1} us"
              .format(i, int(self._servoPos[i])))
      try:
        self._mm18 = servoObj._mm18
      except AttributeError:
        pass

  def set_servo_type(self, i, type):
    """ Change servo type (see `TYPE_xxx`)
    """
    if i in range(self._nChan) and self._Servos[i] is not None:
      self._servo_type[i] = type

  def define_servo_pos(self, _pos):
    """ Define servo position (from angle) without moving the servo,
        e.g. to define the last starting position at power-off
    """
    if len(_pos) == self._nChan:
      for i in range(self._nChan):
        if self._Servos[i] is not None:
          t = self._Servos[i].angle_in_us(_pos[i])
          self._servoPos[i] = t
          self._currPosList[i] = t

  def turn_all_off(self, deinit=False):
    """ Turn all servos off
    """
    for servo in self._Servos:
      if not servo is None:
        servo.off()
        if deinit:
          servo.deinit()

  def deinit(self):
    """ Clean up
    """
    self._Timer.deinit()
    self.turn_all_off(deinit=True)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @timed_function
  def move_timed(self, servos, pos, dt_ms=0):
    self.move(servos, pos, dt_ms, lin_vel)

  #@micropython.native
  def move(self, servos, pos, dt_ms=0, traject=TRJ_LINEAR):
    """ Move the servos in the list to the positions given in `pos`.
        If `dt_ms` > 0, then it will be attempted that all servos reach the
        position at the same time (that is after `dt_ms` ms)
    """
    # Stop ongoing move
    self._isMoving = False

    # Prepare new move
    n = 0
    trj = traject
    nSteps = dt_ms /RATE_MS
    ser = self._Servos
    sdl = self._SIDList
    tpl = self._targetPosList
    spo = self._servoPos
    ssl = self._stepSizeList
    cpl = self._currPosList
    tnl = self._trajNormList
    for iSr, SID in enumerate(servos):
      if not ser[SID]:
        continue
      sdl[n] = SID
      tpl[n] = ser[SID].angle_in_us(pos[iSr])
      if nSteps > 0:
        # A time period is given, therefore calculate the step sizes for this
        # servo's move, with ...
        p = spo[SID]
        if traject == TRJ_SINE:
          ssl[n] = tpl[n] -p  # whole step
          cpl[n] = p          # current position
          if ULAB:
            _a = np.array(
                [np.sin((i+1)/nSteps*np.pi) for i in range(int(nSteps-1))]
              )
            tnl[n] = np.sum(_a) # sum of sine values
          else:
            _a = array.array(
                "f",
                [np.sin((i+1)/nSteps*math.pi) for i in range(int(nSteps-1))]
              )
            tnl[n] = 0
            for j in range(len(_a)):
              tnl[n] += _a[j]
        else:
          # Linear move (each step has the same size)
          s = (tpl[n] -p) /nSteps
          cpl[n] = int(p +s)
          ssl[n] = s
      else:
        # Move directly, therefore update already the final position
        spo[SID] = tpl[iSr]
      n += 1
    self._traject = traject
    self._iStep = 0
    self._nToMove = n
    self._dt_ms = dt_ms
    self._nSteps = int(nSteps)
    self._nStTotal = self._nSteps

    # Initiate move
    if dt_ms == 0:
      # Just move them w/o considering timing
      for iSr in range(n):
        ser[sdl[iSr]].write_us(tpl[iSr])
    else:
      # Setup timer to keep moving them in the requested time
      if self._isFirstMove:
        self._Timer.init(period=RATE_MS, mode=Timer.PERIODIC, callback=self._cb)
        self._isFirstMove = False
      self._isMoving = True

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  #@timed_function
  #@micropython.native
  def _cb(self, value):
    if self._isMoving:
      # Update every servo in the list
      nSt = self._nSteps
      sdl = self._SIDList
      cpl = self._currPosList
      ssl = self._stepSizeList
      tpl = self._targetPosList
      spo = self._servoPos
      ser = self._Servos
      iSr = self._nToMove -1
      iSt = self._iStep
      nST = self._nStTotal
      tnl = self._trajNormList
      while iSr >= 0:
        if not spo[sdl[iSr]] == tpl[iSr]:
          if nSt > 0:
            # Move is ongoing, update servo position ...
            if self._traject == TRJ_SINE:
              cpl[iSr] += ssl[iSr] *np.sin((iSt+1)/nST *np.pi) /tnl[iSr]
              ser[sdl[iSr]].write_us(cpl[iSr])
            else:
              ser[sdl[iSr]].write_us(cpl[iSr])
              cpl[iSr] += ssl[iSr]
          else:
            # Move has ended, therefore set servo to the target position
            spo[sdl[iSr]] = tpl[iSr]
            ser[sdl[iSr]].write_us(spo[sdl[iSr]])
        iSr -= 1
      if nSt > 0:
        self._nSteps = nSt -1
        self._iStep += 1
      else:
        # Move is done
        self._isMoving = False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def is_moving(self):
    """ Returns True if a move is still ongoing
    """
    return self._isMoving

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def calibrate(self, servos=[]):
    """ Interactive calibration of all given servos
    """
    print()
    print("Interactive servo calibration")
    print("=============================")

    servos = servos if len(servos) > 0 else self._servo_number
    new_pos_us = []
    for i in servos:
      temp = []
      r_deg = self._Servos[i].range_deg
      min_us, max_us = self._Servos[i].limits_us

      for j in range(3):
        pos_deg = 0 if j == 0 else r_deg[j-1]
        pos_us = self._Servos[i].angle_in_us(pos_deg)
        self._Servos[i].angle = pos_deg
        print(f"Servo {i:2d}, target angle {pos_deg:4d} deg")
        print(f"-> {self._Servos[i].angle_in_us(pos_deg)} us")
        s = "-"
        while not s.lower() == "y":
          s = input("   `y` for done or increment/decrement in [us]: ").lower()
          dt_us = 0
          try:
            #print("[" +s +"]")
            dt_us = int(s)
          except ValueError:
            if len(s) > 0:
              if s.lower() == "y":
                temp.append([i, pos_deg, pos_us])
                continue
              else:
                print("   Not a number")
          if dt_us != 0:
            pos_us += dt_us
            pos_us = min(max(pos_us, min_us), max_us)
            print(f"   New position [us]: {pos_us}")
            self._Servos[i].write_us(pos_us)
        self._Servos[i].angle = 0
      new_pos_us.append(temp)
    print("---")

    # Print calibration values by servo ...
    for row in new_pos_us:
      delta = row[2][2] -row[1][2]
      print(f"Servo {row[0][0]:2d}: {row[1][1]} = {row[1][2]}, " +
            f"{row[0][1]} = {row[0][2]}, {row[2][1]} = {row[2][2]} "+
            f"(delta = {delta})")
    print("---")
    s = input("Range by [m]in/max or by [c]enter (and delta)? ").lower()
    s = "m" if s[0] == "m" else "c"

    # ... and as Python code
    s0 = "SRV_RANGE_US   = ["
    s1 = "SRV_RANGE_DEG  = ["
    n = len(servos)
    for i in range(n):
      if s == "m":
        s0 += "({0}, {1})".format(new_pos_us[i][1][2], new_pos_us[i][2][2])
        s1 += "({0}, {1})".format(new_pos_us[i][1][1], new_pos_us[i][2][1])
      else:
        delta = new_pos_us[i][2][2] -new_pos_us[i][1][2]
        p0 = new_pos_us[i][0][2] -int(delta/2)
        p1 = new_pos_us[i][0][2] +int(delta/2)
        s0 += "({0}, {1})".format(p0, p1)
        s1 += "({0}, {1})".format(new_pos_us[i][1][1], new_pos_us[i][2][1])

      s0 += ", " if i < n-1 else ""
      s1 += ", " if i < n-1 else ""
    s0 += "]"
    s1 += "]"
    print(s0)
    print(s1)
    print("Done.")

# ----------------------------------------------------------------------------
