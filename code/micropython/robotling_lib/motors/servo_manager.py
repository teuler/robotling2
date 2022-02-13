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
# ----------------------------------------------------------------------------
import gc
import time
import array
from machine import Timer
from robotling_lib.misc.helpers import timed_function
from robotling_lib.platform.platform import platform as pf
import robotling_lib.misc.ansi_color as ansi

# pylint: disable=bad-whitespace
__version__        = "0.1.4.0"
RATE_MS            = const(15)  # 5=hangs, 15...20=ok, 25=not continues
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
    self._nSteps = 0                                      # # of steps to move
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
  def move(self, servos, pos, dt_ms=0):
    """ Move the servos in the list to the positions given in `pos`.
        If `dt_ms` > 0, then it will be attempted that all servos reach the
        position at the same time (that is after `dt_ms` ms)
    """
    # Stop ongoing move
    self._isMoving = False

    # Prepare new move
    n = 0
    nSteps = dt_ms /RATE_MS
    ser = self._Servos
    sdl = self._SIDList
    tpl = self._targetPosList
    spo = self._servoPos
    ssl = self._stepSizeList
    cpl = self._currPosList
    for iS, SID in enumerate(servos):
      if not ser[SID]:
        continue
      sdl[n] = SID
      tpl[n] = ser[SID].angle_in_us(pos[iS])
      if nSteps > 0:
        # A time period is given, therefore calculate the step sizes for this
        # servo's move, with ...
        p = spo[SID]
        s = (tpl[n] -p) /nSteps
        cpl[n] = int(p +s)
        ssl[n] = s
      else:
        # Move directly, therefore update already the final position
        spo[SID] = tpl[iS]
      n += 1
    self._nToMove = n
    self._dt_ms = dt_ms
    self._nSteps = int(nSteps) #-1

    # Initiate move
    if dt_ms == 0:
      # Just move them w/o considering timing
      for iS in range(n):
        ser[sdl[iS]].write_us(tpl[iS])
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
      iS = self._nToMove -1
      while iS >= 0:
        if not spo[sdl[iS]] == tpl[iS]:
          if nSt > 0:
            # Move is ongoing, update servo position ...
            ser[sdl[iS]].write_us(cpl[iS])
            cpl[iS] += ssl[iS]
          else:
            # Move has ended, therefore set servo to the target position
            spo[sdl[iS]] = tpl[iS]
            ser[sdl[iS]].write_us(spo[sdl[iS]])
        iS -= 1
      if nSt > 0:
        self._nSteps = nSt -1
      else:
        # Move is done
        self._isMoving = False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def is_moving(self):
    """ Returns True if a move is still ongoing
    """
    return self._isMoving

# ----------------------------------------------------------------------------
