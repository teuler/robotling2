# ----------------------------------------------------------------------------
# ads1x15.py
# Base class for ADS1015/ADS1115 ADC driver
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
import time
import struct
import array
from micropython import const
from robotling_lib.misc.helpers import timed_function
import robotling_lib.misc.ansi_color as ansi

# pylint: disable=bad-whitespace
_ADS1X15_DEFAULT_ADDRESS         = const(0x48)
_ADS1X15_POINTER_CONVERSION      = const(0x00)
_ADS1X15_POINTER_CONFIG          = const(0x01)
_ADS1X15_CONFIG_OS_SINGLE        = const(0x8000)
_ADS1X15_CONFIG_MUX_OFFSET       = const(12)
_ADS1X15_CONFIG_COMP_QUE_DISABLE = const(0x0003)
_ADS1X15_CONFIG_GAIN             = {
    2 / 3: 0x0000,
    1: 0x0200,
    2: 0x0400,
    4: 0x0600,
    8: 0x0800,
    16: 0x0A00,
  }
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class Mode:
  """An enum-like class representing possible ADC operating modes."""
  # See datasheet "Operating Modes" section
  # values here are masks for setting MODE bit in Config Register
  # pylint: disable=too-few-public-methods
  CONTINUOUS = 0x0000
  SINGLE = 0x0100

# ----------------------------------------------------------------------------
class ADS1x15:
  """Base functionality for ADS1x15 analog to digital converters."""

  def __init__(self, i2c, gain=1, data_rate=None, mode=Mode.SINGLE,
               address=_ADS1X15_DEFAULT_ADDRESS, ):
    """ Requires already initialized I2C bus instance
    """
    self.i2c_device = i2c
    self._i2c_addr = address
    self._last_pin_read = None
    self._data_rate = None
    self._gain = None
    self._mode = None
    self._channelMask = 0x00
    info = self._chip_info()
    self._chan_count = info[3]
    self._shift_fact = info[2]
    self._is_diff = False
    self._data = array.array('i', [0]*self._chan_count)
    self.gain = gain
    self.mode = mode
    self.data_rate = data_rate if data_rate else self._data_rate_default()
    print(ansi.GREEN +"[{0:>12}] {1:35} ({2}): ok"
          .format(info[0], "4-channel A/D", info[1]) +ansi.BLACK)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def data_rate(self):
    """ The data rate for ADC conversion in samples per second
    """
    return self._data_rate

  @data_rate.setter
  def data_rate(self, rate):
    possible_rates = self.rates
    if rate not in possible_rates:
      raise ValueError("Invalid rate.")
    self._data_rate = rate

  @property
  def rates(self):
    """ Possible data rate settings
    """
    raise NotImplementedError("Must be implemented by subclass.")

  @property
  def rate_config(self):
    """ Rate configuration masks
    """
    raise NotImplementedError("Must be implemented by subclass.")

  @property
  def gain(self):
    """ ADC gain
    """
    return self._gain

  @gain.setter
  def gain(self, gain):
    possible_gains = self.gains
    if gain not in possible_gains:
      raise ValueError("Invalid gain.")
    self._gain = gain

  @property
  def gains(self):
    """ Possible gain settings
    """
    g = list(_ADS1X15_CONFIG_GAIN.keys())
    g.sort()
    return g

  @property
  def mode(self):
    """ ADC conversion mode
    """
    return self._mode

  @mode.setter
  def mode(self, mode):
    if mode not in (Mode.CONTINUOUS, Mode.SINGLE):
      raise ValueError("Unsupported mode.")
    self._mode = mode

  @property
  def is_differential(self):
    """ Differential or single-ended
    """
    return self._is_diff

  @is_differential.setter
  def is_differential(self, is_diff):
    self._is_diff = is_diff

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def read_adc(self, chan):
    """ Returns A/D value of channel `chan`
    """
    chan = chan if self._is_diff else chan +0x04
    return self._read(chan)

  @timed_function
  def update_timed(self):
    self.update()

  @micropython.native
  def update(self, is_differential=False):
    """ Updates the A/D data for the channels indicated by the property
        `channelMask`. The data can then be accessed as an array via the
        property "data".
    """
    mk = self._channelMask
    if mk > 0:
      rg = range(self._chan_count)
      da = self._data
      df = self._is_diff
      for i in rg:
        if mk & (0x01 << i):
          chan = i if df else i +0x04
          da[i] = self._read(chan)

  @property
  def data(self):
    """ Array with A/D data
    """
    return self._data

  @property
  def channel_count(self):
    return self._chan_count

  @property
  def max_value(self):
    return 2**self.bits

  @property
  def channel_mask(self):
    return self._channelMask

  @channel_mask.setter
  def channel_mask(self, value):
    value &= 0x0f
    self._channelMask = value

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _data_rate_default(self):
    """ Retrieve the default data rate for this ADC (in samples per second).
    """
    raise NotImplementedError("Must be implemented by subclass.")

  @micropython.native
  def _read(self, pin):
    """ Perform an ADC read. Returns the signed integer result of the read.
    """
    # Immediately return conversion register result if in CONTINUOUS mode
    # and pin has not changed
    if self.mode == Mode.CONTINUOUS and self._last_pin_read == pin:
      raw_adc = self._read_register(_ADS1X15_POINTER_CONVERSION, True)
      raw_adc = raw_adc.to_bytes(2, "big")
      return struct.unpack(">h", raw_adc)[0] >> self._shift_fact

    # Assign last pin read if in SINGLE mode or first sample in CONTINUOUS
    # mode on this pin
    self._last_pin_read = pin

    # Configure ADC every time before a conversion in SINGLE mode
    # or changing channels in CONTINUOUS mode
    config = _ADS1X15_CONFIG_OS_SINGLE if self.mode == Mode.SINGLE else 0
    config |= (pin & 0x07) << _ADS1X15_CONFIG_MUX_OFFSET
    config |= _ADS1X15_CONFIG_GAIN[self.gain]
    config |= self.mode
    config |= self.rate_config[self.data_rate]
    config |= _ADS1X15_CONFIG_COMP_QUE_DISABLE
    self._write_register(_ADS1X15_POINTER_CONFIG, config)

    # Wait for conversion to complete
    # ADS1x1x devices settle within a single conversion cycle
    if self.mode == Mode.SINGLE:
      # Continuously poll conversion complete status bit
      #while not self._conversion_complete():
      while not self._read_register(_ADS1X15_POINTER_CONFIG) & 0x8000:
        pass
    else:
      # Can't poll registers in CONTINUOUS mode
      # Wait expected time for two conversions to complete
      time.sleep(2 /self.data_rate)

    raw_adc = self._read_register(_ADS1X15_POINTER_CONVERSION, False)
    raw_adc = raw_adc.to_bytes(2, "big")
    return struct.unpack(">h", raw_adc)[0] >> self._shift_fact

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _write_register(self, reg, value):
    """ Write 16 bit value to register.
    """
    _buf = bytearray([reg, (value >> 8) & 0xFF, value & 0xFF])
    with self.i2c_device as i2c:
      i2c.writeto(self._i2c_addr, _buf)

  def _read_register(self, reg, fast=False):
    """ Read 16 bit register value. If fast is True, the pointer register
        is not updated.
    """
    _buf = bytearray(3)
    _reg = bytearray([reg])
    with self.i2c_device as i2c:
      if fast:
        i2c.readfrom_into(self._i2c_addr, _buf)
      else:
        i2c.write_then_readinto(self._i2c_addr, _reg, _buf, in_end=2)
    return _buf[0] << 8 | _buf[1]

# ----------------------------------------------------------------------------
