# ----------------------------------------------------------------------------
# pololu_lidar_ranging.py
# Pololu lidar-based distance ranging sensors
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-05-02, v1
# ----------------------------------------------------------------------------
from micropython import const
from machine import Pin, time_pulse_us
from robotling_lib.sensors.sensor_base import SensorBase

# pylint: disable=bad-whitespace
__version__    = "0.1.0.0"
CHIP_NAME      = "IRS16A"
TIMEOUT_US     = const(200000)
N_REREADS      = const(3)
ERR_TIMEOUT    = const(-1)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class PololuLidarRangingSensor(SensorBase):
  """Class for pulse-width Pololu lidar-based ranging sensor."""

  def __init__(self, pin):
    super().__init__(driver=None, chan=1)
    self._pin = Pin(pin)
    self._type = "Lidar-based range"

  @property
  def range_raw(self):
    return time_pulse_us(self._pin, 1, TIMEOUT_US)

  @micropython.native
  @property
  def range_cm(self):
    t = 0
    p = self._pin
    n = N_REREADS
    while (t := time_pulse_us(p, 1, TIMEOUT_US)) < 1000 and n > 0:
      n -= 1
    if t < 0 or n == 0:
      return ERR_TIMEOUT
    else:
      return 0.75 *(t -1000) /10

# ----------------------------------------------------------------------------
