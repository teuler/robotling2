# ----------------------------------------------------------------------------
# ads1115.py
# Class for ADS1115 ADC driver
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
from -ads1x15 import ADS1x15, Mode

__version__ = "0.1.0.0"
CHIP_NAME   = "ads1115"
CHAN_COUNT  = const(4)
SHIFT_FACT  = const(0) # value >> 0

# Data sample rates
_ADS1115_CONFIG_DR = {
  8: 0x0000,
  16: 0x0020,
  32: 0x0040,
  64: 0x0060,
  128: 0x0080,
  250: 0x00A0,
  475: 0x00C0,
  860: 0x00E0,
}

# ----------------------------------------------------------------------------
class ADS1115(ADS1x15):
  """Class for the ADS1115 16 bit ADC."""

  @property
  def bits(self):
    return 16

  @property
  def rates(self):
    r = list(_ADS1115_CONFIG_DR.keys())
    r.sort()
    return r

  @property
  def rate_config(self):
    return _ADS1115_CONFIG_DR

  def _data_rate_default(self):
    return 128

  def _chip_info(self):
    return CHIP_NAME, __version__, SHIFT_FACT, CHAN_COUNT

# ----------------------------------------------------------------------------
