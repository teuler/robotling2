# ----------------------------------------------------------------------------
# aio.py
#
# Basic analog pin support
# (for rp2 micropython)
#
# The MIT License (MIT)
# Copyright (c) 2021-22 Thomas Euler
# 2021-02-28, v1.0
# ----------------------------------------------------------------------------
import time
import array
from micropython import const
from machine import ADC

# pylint: disable=bad-whitespace
__version__     = "0.1.0.0"

CHAN_COUNT      = const(1)
MAX_VALUE       = const(65535)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class AnalogIn(object):
  """Basic analog input."""

  def __init__(self, pin):
    self._pin = ADC(pin)

  def deinit(self):
    self._pin = None

  @property
  def value(self):
    return self._pin.read_u16()

  @property
  def max_adc(self):
    return MAX_VALUE

# ----------------------------------------------------------------------------
class AnalogIn_Driver(object):
  """Mock driver for build-in ADC."""

  def __init__(self, pin):
    """ Requires an ADC enabled pin.
    """
    self._pin = ADC(pin)
    self._data = array.array("I", [0])

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def readADC(self, chan):
    """ Returns error code and A/D value of channel `chan` as tuple; here
        only `chan` == 0 is allowed
    """
    assert chan == 0, "readADC error: `chan` must be 0"
    return self._pin.read_u16()

  def update(self):
    """ Updates the A/D data for the channel; implemented for compatibility
        reasons.
    """
    self._data[0] = self._pin.read_u16()

  @property
  def data(self):
    """ Array with A/D data
    """
    return self._data

  @property
  def channelCount(self):
    return CHAN_COUNT

  @property
  def maxValue(self):
    return MAX_VALUE

  @property
  def channelMask(self):
    return 0x01

  @channelMask.setter
  def channelMask(self, value):
    pass

# ----------------------------------------------------------------------------
