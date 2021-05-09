# ----------------------------------------------------------------------------
# ads1015.py
# Class for ADS1015 ADC driver
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-05-05, v1
#
# Based on the CircuitPython driver:
# https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
#
# The MIT License (MIT)
# Copyright (c) 2018 Carter Nelson
# ----------------------------------------------------------------------------
from .ads1x15 import ADS1x15, Mode

__version__ = "0.1.0.0"
CHIP_NAME   = "ads1015"
CHAN_COUNT  = const(4)
SHIFT_FACT  = const(3) # value >> 3; why 4 in the Adafruit driver?!

# Data sample rates
_ADS1015_CONFIG_DR = {
  128: 0x0000,
  250: 0x0020,
  490: 0x0040,
  920: 0x0060,
  1600: 0x0080,
  2400: 0x00A0,
  3300: 0x00C0,
}

# ----------------------------------------------------------------------------
class ADS1015(ADS1x15):
  """Class for the ADS1015 12 bit ADC."""

  @property
  def bits(self):
    return 12

  @property
  def rates(self):
    r = list(_ADS1015_CONFIG_DR.keys())
    r.sort()
    return r

  @property
  def rate_config(self):
    return _ADS1015_CONFIG_DR

  def _data_rate_default(self):
    return 1600

  def _chip_info(self):
    return CHIP_NAME, __version__, SHIFT_FACT, CHAN_COUNT

# ----------------------------------------------------------------------------
