# ----------------------------------------------------------------------------
# rbl2_gait.py
#
# Gait control for robotling2
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-03-03, v1.0
# ----------------------------------------------------------------------------
import time
import array
import rbl2_global as glb
import rbl2_config as cfg
from micropython import const
from robotling_lib.motors.servo import Servo
from robotling_lib.motors.servo_manager import ServoManager

# pylint: disable=bad-whitespace
__version__  = "0.1.0.0"

#                Servos,  Positions, Dur, Mode,           Next, Jump
GAIT_SEQ     = [([2],     [ 20],     250, glb.STATE_WALKING,   1,   4),     # 0
                ([0,1],   [ 40, 40], 400, glb.STATE_WALKING,   2,   None),  # 1
                ([2],     [-20],     250, glb.STATE_WALKING,   3,   4),     # 2
                ([0,1],   [-40,-40], 400, glb.STATE_WALKING,   0,   None),  # 3
                ([0,1],   [  0,  0], 400, glb.STATE_STOPPING,  5,   5),     # 4
                ([2],     [  0],     400, glb.STATE_STOPPING, -1,  None)]   # 5
GS_SRV       = const(0)
GS_POS       = const(1)
GS_DUR       = const(2)
GS_MODE      = const(3)
GS_NEXT      = const(4)
GS_JUMP      = const(5)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class Gait(object):
  """Gait control"""

  def __init__(self, verbose=False):
    # Initializing ...
    self._state = glb.STATE_NONE
    self._iStep = 0
    self._vel = 1.
    self._dir = 0.
    self._verbose = verbose

    # Configure servos and servo manager
    self._Servos = []
    self._SM = ServoManager(len(cfg.SRV_ID))
    for i, pin in enumerate(cfg.SRV_PIN):
      srv = Servo(pin, us_range=cfg.SRV_RANGE_US[i],
                  ang_range=cfg.SRV_RANGE_DEG[i])
#      print (pin, cfg.SRV_RANGE_US[i], cfg.SRV_RANGE_DEG[i])
      self._Servos.append(srv)
      self._SM.add_servo(cfg.SRV_ID[i], srv)

    # Getting ready
    self.neutral()
    time.sleep_ms(1000)
    self._state = glb.STATE_IDLE
    if self._verbose:
      glb.toLog("Gait control ready.")

  def deinit(self):
    """ Shutting down gait control
    """
    self._state = glb.STATE_POWERING_DOWN
    self.neutral(dt=500)
    time.sleep_ms(550)
    self._SM.deinit()
    if self._verbose:
      glb.toLog("Gait control off.")
    self._state = glb.STATE_OFF

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def neutral(self, dt=0):
    """ Assume neutral position
    """
    if self._verbose:
      print("Assuming neutral position ...")
    self._SM.move([0,1,2], [0,0,0], dt)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def walk(self):
    """ Start walking, defined by the properties `direction` (e.g. -1=left
        turn, +1=right turn, 0=straight forward) and `velocity` (<0, slower,
        >1 faster)
    """
    self._state = glb.STATE_WALKING if self._dir == 0 else glb.STATE_TURNING
    self._iStep = 0
    self.spin()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stop(self):
    """ Stop movement gracefully
    """
    self._state = glb.STATE_STOPPING
    self.spin()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def spin(self):
    """ Keep robot moving; needs to be called frequently
    """
    st = self._state
    sm = self._SM
    if st == glb.STATE_IDLE or sm.is_moving:
      return

    iS = self._iStep
    dr = self._dir
    if st in [glb.STATE_WALKING, glb.STATE_TURNING, glb.STATE_STOPPING]:
      # Apply direction
      pos = array.array("f", GAIT_SEQ[iS][GS_POS])
      for j, id in enumerate(GAIT_SEQ[iS][GS_SRV]):
        if dr < 0:
          if id == 0:
            pos[j] *= -abs(dr)
        elif dr > 0:
          if id == 1:
            pos[j] *= -abs(dr)

      # Execute move
      vel = int(GAIT_SEQ[iS][GS_DUR] *self._vel)
      sm.move(GAIT_SEQ[iS][GS_SRV], pos, vel)

      # Determine next move in sequence, depending on whether a stop was
      # issued or not
      iN = GAIT_SEQ[iS][GS_NEXT]
      iJ = GAIT_SEQ[iS][GS_JUMP]
      if st in [glb.STATE_WALKING, glb.STATE_TURNING]:
        # Just continue walking ...
        self._iStep = iN
      elif st == glb.STATE_STOPPING:
        if GAIT_SEQ[iS][GS_MODE] in [glb.STATE_WALKING, glb.STATE_TURNING]:
          # Just received "stop"; jump to stopping sequence if available
          self._iStep = iJ if iJ is not None else iN
        else:
          # Stopping is ongoing ...
          self._iStep = iN
          if iN < 0:
            # Stopped
            self._state = glb.STATE_IDLE
      else:
        print("Not implemented")

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def state(self):
    return self._state

  @property
  def direction(self):
    return self._dir

  @direction.setter
  def direction(self, value):
    self._dir = max(min(value, 1.0), -1.0)

  @property
  def velocity(self):
    return self.vel

  @velocity.setter
  def velocity(self, vel):
    self._vel = max(vel, 0.1)

# ----------------------------------------------------------------------------
