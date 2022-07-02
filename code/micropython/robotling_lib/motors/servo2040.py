# ----------------------------------------------------------------------------
# servo2040.py
# Encapsulates Pimoroni's servo class
#
# The MIT License (MIT)
# Copyright (c) 2022 Thomas Euler
# 2022-05-04, v1
# ----------------------------------------------------------------------------
import array
import robotling_lib.misc.ansi_color as ansi
from robotling_lib.misc.helpers import timed_function
from robotling_lib.motors.servo_base import ServoBase
from servo import Servo as _Servo

# pylint: disable=bad-whitespace
__version__        = "0.1.0.0"
DEF_RANGE_DEG      = (0, 180)
DEF_RANGE_US       = (500, 2500)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class Servo(ServoBase):
  """Simplified interface class for Pimoroni's Servo class."""

  def __init__(self, pin, freq=50, us_range=DEF_RANGE_US,
               ang_range=DEF_RANGE_DEG, us_limits=DEF_RANGE_US,
               verbose=False):
    """ Initialises the pin that connects to the servo, with `pin` as a pin
        number, the frequency `freq` of the signal (in Hz), the timing
        (`us_range`) for the given angular range (`ang_range`), and the
        timing limits (`us_limits`).
        If `verbose` == True then angle and timing is logged; useful for
        setting up a new servo (range).
    """
    super().__init__(freq, us_range, ang_range, us_limits, verbose)
    self._srv = _Servo(pin)
    if verbose:
      print("Servo at pin {0} ({1} Hz) ready.".format(pin, freq))

  @property
  def angle(self):
    """ Report current angle (in degrees)
    """
    return self._angle

  @angle.setter
  def angle(self, value):
    """ Move to the specified angle (in degrees)
    """
    self.write_us(self.angle_in_us(value))

  def off(self):
    """ Turn servo off
    """
    self._srv.disable()

  def deinit(self):
    """ Deinitialize PWM for given pin
    """
    try:
      self._srv.disable()
    except:
      pass

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @timed_function
  def write_us_timed(self, t_us):
    self._write_us(t_us)

  def write_us(self, t_us):
    """ Move to a position given by the timing
    """
    self._srv.pulse(t_us)
    if self._verbose:
      print("angle={0}, t_us={1}".format(self._srv.value(), t_us))

# ----------------------------------------------------------------------------
