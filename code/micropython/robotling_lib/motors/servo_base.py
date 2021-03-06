# ----------------------------------------------------------------------------
# servo_base.py
# Base class for servos
#
# The MIT License (MIT)
# Copyright (c) 2018-2022 Thomas Euler
# 2020-01-04, v1
# 2022-05-05, v1.7, support limits to the timing
# ----------------------------------------------------------------------------
import array

# pylint: disable=bad-whitespace
__version__        = "0.1.0.0"
# pylint: enabled=bad-whitespace

# ----------------------------------------------------------------------------
class ServoBase(object):
  """Base class for servos."""

  def __init__(self, freq, us_range, ang_range, us_limits, verbose):
    """ Initialises the servo structure using the frequency `freq` of the
        signal (in Hz), the timing (`us_range`) for the given angular range
        (`ang_range`) covered, and the timing limits (`us_limits`).
        If `verbose` == True then angle and timing is logged; useful for
        setting up a new servo (range).
    """
    self._verbose = verbose
    self._freq = freq
    self._angle = 0
    self._pwm = None
    self._max_duty = 0
    self._range = array.array('i', [0]*8)
    self._sign = 1
    self._speed = 0
    self._accel = 0
    self.change_range(us_range, ang_range, us_limits)

  def change_range(self, us_range, ang_range=[-90, 90],
                   us_limits=[500,2500], _sign=1):
    """ Sets the minimun and maximum supported timing (`us_range`), and the
        respective angular range (`ang_range`) covered; `_sign` determines the
        sign of the input angle
    """
    self._range[0] = int(us_range[0])
    self._range[1] = int(us_range[1])
    self._range[2] = int(us_range[1] -us_range[0])
    self._invert = ang_range[0] > ang_range[1]
    self._range[3] = int(min(ang_range[0], ang_range[1]))
    self._range[4] = int(max(ang_range[0], ang_range[1]))
    self._range[5] = int(abs(ang_range[1] -ang_range[0]))
    self._range[6] = int(us_limits[0])
    self._range[7] = int(us_limits[1])
    self._sign = -1 if _sign < 0 else 1

  def change_behavior(self, speed, accel):
    self._speed = speed if speed >= 0 and speed <= 255 else self._speed
    self._accel = accel if accel >= 0 and accel <= 255 else self._accel

  @property
  def range_us(self):
    return self._range[0], self._range[1]

  @property
  def range_deg(self):
    return self._range[3], self._range[4]

  @property
  def limits_us(self):
    return self._range[6], self._range[7]

  @property
  def angle(self):
    return self._angle *self._sign

  @angle.setter
  def angle(self, value):
    raise NotImplementedError()

  def off(self):
    raise NotImplementedError()

  def deinit(self):
    pass

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def angle_in_us(self, angle=None):
    """ Return the angle as timing value
    """
    r = self._range
    if not angle is None:
      self._angle = min(r[4], max(r[3], angle)) *self._sign
    return int(r[0] +r[2] *(self._angle -r[3]) //r[5])

# ----------------------------------------------------------------------------
