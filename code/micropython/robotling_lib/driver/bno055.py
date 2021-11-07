# ----------------------------------------------------------------------------
# bno055.py
# Class for BNO055 9-DOF IMU fusion breakout
#
# The MIT License (MIT)
# Copyright (c) 2020 Thomas Euler
# 2020-09-07, v1
#
# Based on the CircuitPython driver:
# https://github.com/adafruit/Adafruit_CircuitPython_BNO055
#
# This is a CircuitPython driver for the Bosch BNO055 nine degree of freedom
# inertial measurement unit module with sensor fusion.
#
# The MIT License (MIT)
# Copyright (c) 2017 Radomir Dopieralski for Adafruit Industries.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ----------------------------------------------------------------------------
try:
  import struct
except ImportError:
  import ustruct as struct

from micropython import const
import robotling_lib.misc.ansi_color as ansi
from robotling_lib.platform.platform import platform
if platform.languageID == platform.LNG_MICROPYTHON:
  import time
  from robotling_lib.platform.esp32.register.i2c_struct \
    import Struct, UnaryStruct
elif platform.languageID == platform.LNG_CIRCUITPYTHON:
  import robotling_lib.platform.circuitpython.time as time
  from robotling_lib.platform.circuitpython.register.i2c_struct \
    import Struct, UnaryStruct
else:
  print(ansi.RED +"ERROR: No matching libraries in `platform`." +ansi.BLACK)

__version__ = "0.1.0.0"
CHIP_NAME   = "bno055"
CHAN_COUNT  = const(1)

# pylint: disable=bad-whitespace
_CHIP_ID                = const(0xA0)
ADDRESS_BNO055          = const(0x28)

CONFIG_MODE             = const(0x00)
ACCONLY_MODE            = const(0x01)
MAGONLY_MODE            = const(0x02)
GYRONLY_MODE            = const(0x03)
ACCMAG_MODE             = const(0x04)
ACCGYRO_MODE            = const(0x05)
MAGGYRO_MODE            = const(0x06)
AMG_MODE                = const(0x07)
IMUPLUS_MODE            = const(0x08)
COMPASS_MODE            = const(0x09)
M4G_MODE                = const(0x0A)
NDOF_FMC_OFF_MODE       = const(0x0B)
NDOF_MODE               = const(0x0C)

ACCEL_2G                = const(0x00)  # For accel_range property
ACCEL_4G                = const(0x01)  # Default
ACCEL_8G                = const(0x02)
ACCEL_16G               = const(0x03)
ACCEL_7_81HZ            = const(0x00)  # For accel_bandwidth property
ACCEL_15_63HZ           = const(0x04)
ACCEL_31_25HZ           = const(0x08)
ACCEL_62_5HZ            = const(0x0C)  # Default
ACCEL_125HZ             = const(0x10)
ACCEL_250HZ             = const(0x14)
ACCEL_500HZ             = const(0x18)
ACCEL_1000HZ            = const(0x1C)
ACCEL_NORMAL_MODE       = const(0x00)  # Default. For accel_mode property
ACCEL_SUSPEND_MODE      = const(0x20)
ACCEL_LOWPOWER1_MODE    = const(0x40)
ACCEL_STANDBY_MODE      = const(0x60)
ACCEL_LOWPOWER2_MODE    = const(0x80)
ACCEL_DEEPSUSPEND_MODE  = const(0xA0)

GYRO_2000_DPS           = const(0x00)  # Default. For gyro_range property
GYRO_1000_DPS           = const(0x01)
GYRO_500_DPS            = const(0x02)
GYRO_250_DPS            = const(0x03)
GYRO_125_DPS            = const(0x04)
GYRO_523HZ              = const(0x00)  # For gyro_bandwidth property
GYRO_230HZ              = const(0x08)
GYRO_116HZ              = const(0x10)
GYRO_47HZ               = const(0x18)
GYRO_23HZ               = const(0x20)
GYRO_12HZ               = const(0x28)
GYRO_64HZ               = const(0x30)
GYRO_32HZ               = const(0x38)  # Default
GYRO_NORMAL_MODE        = const(0x00)  # Default. For gyro_mode property
GYRO_FASTPOWERUP_MODE   = const(0x01)
GYRO_DEEPSUSPEND_MODE   = const(0x02)
GYRO_SUSPEND_MODE       = const(0x03)
GYRO_ADVPOWERSAVE_MODE  = const(0x04)

MAGNET_2HZ              = const(0x00)  # For magnet_rate property
MAGNET_6HZ              = const(0x01)
MAGNET_8HZ              = const(0x02)
MAGNET_10HZ             = const(0x03)
MAGNET_15HZ             = const(0x04)
MAGNET_20HZ             = const(0x05)  # Default
MAGNET_25HZ             = const(0x06)
MAGNET_30HZ             = const(0x07)
MAGNET_LOWPOWER_MODE    = const(0x00)  # For magnet_operation_mode property
MAGNET_REGULAR_MODE     = const(0x08)  # Default
MAGNET_ENHREGULAR_MODE  = const(0x10)
MAGNET_ACCURACY_MODE    = const(0x18)
MAGNET_NORMAL_MODE      = const(0x00)  # for magnet_power_mode property
MAGNET_SLEEP_MODE       = const(0x20)
MAGNET_SUSPEND_MODE     = const(0x40)
MAGNET_FORCEMODE_MODE   = const(0x60)  # Default

_POWER_NORMAL           = const(0x00)
_POWER_LOW              = const(0x01)
_POWER_SUSPEND          = const(0x02)

_MODE_REGISTER          = const(0x3D)
_PAGE_REGISTER          = const(0x07)
_ACCEL_CONFIG_REGISTER  = const(0x08)
_MAGNET_CONFIG_REGISTER = const(0x09)
_GYRO_CONFIG_0_REGISTER = const(0x0A)
_GYRO_CONFIG_1_REGISTER = const(0x0B)
_CALIBRATION_REGISTER   = const(0x35)
_OFFSET_ACCEL_REGISTER  = const(0x55)
_OFFSET_MAGNET_REGISTER = const(0x5B)
_OFFSET_GYRO_REGISTER   = const(0x61)
_RADIUS_ACCEL_REGISTER  = const(0x67)
_RADIUS_MAGNET_REGISTER = const(0x69)
_TRIGGER_REGISTER       = const(0x3F)
_POWER_REGISTER         = const(0x3E)
_ID_REGISTER            = const(0x00)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class _ScaledReadOnlyStruct(Struct):
  # pylint: disable=too-few-public-methods
  def __init__(self, register_address, struct_format, scale):
    super(_ScaledReadOnlyStruct, self).__init__(register_address, struct_format)
    self.scale = scale

  def __get__(self, obj, objtype=None):
    result = super(_ScaledReadOnlyStruct, self).__get__(obj, objtype)
    return tuple(self.scale*v for v in result)

  def __set__(self, obj, value):
    raise NotImplementedError()


class _ReadOnlyUnaryStruct(UnaryStruct):
  # pylint: disable=too-few-public-methods
  def __set__(self, obj, value):
    raise NotImplementedError()


class _ModeStruct(Struct):
  # pylint: disable=too-few-public-methods
  def __init__(self, register_address, struct_format, mode):
    super().__init__(register_address, struct_format)
    self.mode = mode

  def __get__(self, obj, objtype=None):
    last_mode = obj.mode
    obj.mode = self.mode
    result = super().__get__(obj, objtype)
    obj.mode = last_mode
    # single value comes back as a one-element tuple
    return result[0] if isinstance(result, tuple) and len(result) == 1 else result

  def __set__(self, obj, value):
    last_mode = obj.mode
    obj.mode = self.mode
    # underlying __set__() expects a tuple
    set_val = value if isinstance(value, tuple) else (value,)
    super().__set__(obj, set_val)
    obj.mode = last_mode

# ----------------------------------------------------------------------------
class BNO055Base(object):
  """Base class for the BNO055 9DOF IMU sensor."""

  def __init__(self, i2c=None):
    """ Requires already initialized I2C bus instance.
    """
    if i2c:
      self.i2c_device = i2c
    self._isReady = False
    chip_id = self._read_register(_ID_REGISTER)
    if chip_id != _CHIP_ID:
      raise RuntimeError("Bad chip id ({0} != {1})".format(chip_id, _CHIP_ID))
    self._reset()
    self._write_register(_POWER_REGISTER, _POWER_NORMAL)
    self._write_register(_PAGE_REGISTER, 0x00)
    self._write_register(_TRIGGER_REGISTER, 0x00)
    self.accel_range = ACCEL_4G
    self.gyro_range = GYRO_2000_DPS
    self.magnet_rate = MAGNET_20HZ
    time.sleep_ms(10)
    self.mode = NDOF_MODE
    time.sleep_ms(10)

    self._isReady = True
    c = ansi.GREEN if self._isReady else ansi.RED
    print(c +"[{0:>12}] {1:35} ({2}): {3}"
          .format(CHIP_NAME, "NNO055 9DOF IMU sensor", __version__,
                  "ok" if self._isReady else "NOT FOUND") +ansi.BLACK)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _reset(self):
    """ Resets the sensor to default settings.
    """
    self.mode = CONFIG_MODE
    try:
      self._write_register(_TRIGGER_REGISTER, 0x20)
    except OSError:
      pass
    # Wait for the chip to reset (650 ms typ.)
    time.sleep_ms(700)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  @property
  def mode(self):
    """ legend: x=on, -=off
        +------------------+-------+---------+------+----------+
        | Mode             | Accel | Compass | Gyro | Absolute |
        +==================+=======+=========+======+==========+
        | CONFIG_MODE      |   -   |   -     |  -   |     -    |
        +------------------+-------+---------+------+----------+
        | ACCONLY_MODE     |   X   |   -     |  -   |     -    |
        +------------------+-------+---------+------+----------+
        | MAGONLY_MODE     |   -   |   X     |  -   |     -    |
        +------------------+-------+---------+------+----------+
        | GYRONLY_MODE     |   -   |   -     |  X   |     -    |
        +------------------+-------+---------+------+----------+
        | ACCMAG_MODE      |   X   |   X     |  -   |     -    |
        +------------------+-------+---------+------+----------+
        | ACCGYRO_MODE     |   X   |   -     |  X   |     -    |
        +------------------+-------+---------+------+----------+
        | MAGGYRO_MODE     |   -   |   X     |  X   |     -    |
        +------------------+-------+---------+------+----------+
        | AMG_MODE         |   X   |   X     |  X   |     -    |
        +------------------+-------+---------+------+----------+
        | IMUPLUS_MODE     |   X   |   -     |  X   |     -    |
        +------------------+-------+---------+------+----------+
        | COMPASS_MODE     |   X   |   X     |  -   |     X    |
        +------------------+-------+---------+------+----------+
        | M4G_MODE         |   X   |   X     |  -   |     -    |
        +------------------+-------+---------+------+----------+
        | NDOF_FMC_OFF_MODE|   X   |   X     |  X   |     X    |
        +------------------+-------+---------+------+----------+
        | NDOF_MODE        |   X   |   X     |  X   |     X    |
        +------------------+-------+---------+------+----------+

        The default mode is ``NDOF_MODE``.
        | You can set the mode using the line below:
        | ``sensor.mode = adafruit_bno055.ACCONLY_MODE``
        | replacing ``ACCONLY_MODE`` with the mode you want to use

        .. data:: CONFIG_MODE

          This mode is used to configure BNO, wherein all output data is reset
          to zero and sensor fusion is halted.

        .. data:: ACCONLY_MODE

          In this mode, the BNO055 behaves like a stand-alone acceleration
          sensor. In this mode the other sensors (magnetometer, gyro) are
          suspended to lower the power consumption.

        .. data:: MAGONLY_MODE

        	In MAGONLY mode, the BNO055 behaves like a stand-alone magnetometer,
          with acceleration sensor and gyroscope being suspended.

        .. data:: GYRONLY_MODE

          In GYROONLY mode, the BNO055 behaves like a stand-alone gyroscope,
          with acceleration sensor and magnetometer being suspended.

        .. data:: ACCMAG_MODE

          Both accelerometer and magnetometer are switched on, the user can
          read the data from these two sensors.

        .. data:: ACCGYRO_MODE

          Both accelerometer and gyroscope are switched on; the user can read
          the data from these two sensors.

        .. data:: MAGGYRO_MODE

          Both magnetometer and gyroscope are switched on, the user can read
          the data from these two sensors.

        .. data:: AMG_MODE

          All three sensors accelerometer, magnetometer and gyroscope are
          switched on.

        .. data:: IMUPLUS_MODE

          In the IMU mode the relative orientation of the BNO055 in space is
          calculated from the accelerometer and gyroscope data. The
          calculation is fast (i.e. high output data rate).

        .. data:: COMPASS_MODE

          The COMPASS mode is intended to measure the magnetic earth field
          and calculate the geographic direction.

        .. data:: M4G_MODE

          The M4G mode is similar to the IMU mode, but instead of using the
          gyroscope signal to detect rotation, the changing orientation of
          the magnetometer in the magnetic field is used.

        .. data:: NDOF_FMC_OFF_MODE

          This fusion mode is same as NDOF mode, but with the Fast
          Magnetometer Calibration turned ‘OFF’.

        .. data:: NDOF_MODE

          This is a fusion mode with 9 degrees of freedom where the fused
          absolute orientation data is calculated from accelerometer,
          gyroscope and the magnetometer.
    """
    return self._read_register(_MODE_REGISTER)

  @mode.setter
  def mode(self, new_mode):
    self._write_register(_MODE_REGISTER, CONFIG_MODE)  # Empirically necessary
    time.sleep_ms(20)  # Datasheet table 3.6
    if new_mode != CONFIG_MODE:
      self._write_register(_MODE_REGISTER, new_mode)
      time.sleep_ms(10)  # Table 3.6

  @property
  def calibration_status(self):
    """ Tuple containing sys, gyro, accel, and mag calibration data.
    """
    calibration_data = self._read_register(_CALIBRATION_REGISTER)
    sys = (calibration_data >> 6) & 0x03
    gyro = (calibration_data >> 4) & 0x03
    accel = (calibration_data >> 2) & 0x03
    mag = calibration_data & 0x03
    return sys, gyro, accel, mag

  @property
  def calibrated(self):
    """ Boolean indicating calibration status.
    """
    sys, gyro, accel, mag = self.calibration_status
    return sys == gyro == accel == mag == 0x03

  @property
  def external_crystal(self):
    """ Switches the use of external crystal on or off.
    """
    last_mode = self.mode
    self.mode = CONFIG_MODE
    self._write_register(_PAGE_REGISTER, 0x00)
    value = self._read_register(_TRIGGER_REGISTER)
    self.mode = last_mode
    return value == 0x80

  @external_crystal.setter
  def use_external_crystal(self, value):
    last_mode = self.mode
    self.mode = CONFIG_MODE
    self._write_register(_PAGE_REGISTER, 0x00)
    self._write_register(_TRIGGER_REGISTER, 0x80 if value else 0x00)
    self.mode = last_mode
    time.sleep_ms(10)

  @property
  def temperature(self):
    """ Measures the temperature of the chip in degrees Celsius.
    """
    return self._temperature

  @property
  def _temperature(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def acceleration(self):
    """ Gives the raw accelerometer readings, in m/s.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode not in [0x00, 0x02, 0x03, 0x06]:
      return self._acceleration
    return (None, None, None)

  @property
  def _acceleration(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def magnetic(self):
    """ Gives the raw magnetometer readings in microteslas.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode not in [0x00, 0x03, 0x05, 0x08]:
      return self._magnetic
    return (None, None, None)

  @property
  def _magnetic(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def gyro(self):
    """ Gives the raw gyroscope reading in radians per second.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode not in [0x00, 0x01, 0x02, 0x04, 0x09, 0x0A]:
      return self._gyro
    return (None, None, None)

  @property
  def _gyro(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def euler(self):
    """ Gives the calculated orientation angles, in degrees.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode in [0x09, 0x0B, 0x0C]:
      return self._euler
    return (None, None, None)

  @property
  def _euler(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def quaternion(self):
    """ Gives the calculated orientation as a quaternion.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode in [0x09, 0x0B, 0x0C]:
      return self._quaternion
    return (None, None, None, None)

  @property
  def _quaternion(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def linear_acceleration(self):
    """ Returns the linear acceleration, without gravity, in m/s.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode in [0x09, 0x0B, 0x0C]:
      return self._linear_acceleration
    return (None, None, None)

  @property
  def _linear_acceleration(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def gravity(self):
    """ Returns the gravity vector, without acceleration in m/s.
        Returns an empty tuple of length 3 when this property has been
        disabled by the current mode.
    """
    if self.mode in [0x09, 0x0B, 0x0C]:
      return self._gravity
    return (None, None, None)

  @property
  def _gravity(self):
    raise NotImplementedError("Must be implemented.")

  @property
  def accel_range(self):
    """ Switch the accelerometer range and return the new range.
        Default value: +/- 4g; see table 3-8 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00000011 & value

  @accel_range.setter
  def accel_range(self, rng=ACCEL_4G):
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    masked_value = 0b11111100 & value
    self._write_register(_ACCEL_CONFIG_REGISTER, masked_value | rng)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def accel_bandwidth(self):
    """ Switch the accelerometer bandwidth and return the new bandwidth.
        Default value: 62.5 Hz; see table 3-8 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00011100 & value

  @accel_bandwidth.setter
  def accel_bandwidth(self, bandwidth=ACCEL_62_5HZ):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    masked_value = 0b11100011 & value
    self._write_register(_ACCEL_CONFIG_REGISTER, masked_value | bandwidth)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def accel_mode(self):
    """ Switch the accelerometer mode and return the new mode.
        Default value: Normal; see table 3-8 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b11100000 & value

  @accel_mode.setter
  def accel_mode(self, mode=ACCEL_NORMAL_MODE):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_ACCEL_CONFIG_REGISTER)
    masked_value = 0b00011111 & value
    self._write_register(_ACCEL_CONFIG_REGISTER, masked_value | mode)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def gyro_range(self):
    """ Switch the gyroscope range and return the new range.
        Default value: 2000 dps; see table 3-9 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_0_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00000111 & value

  @gyro_range.setter
  def gyro_range(self, rng=GYRO_2000_DPS):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_0_REGISTER)
    masked_value = 0b00111000 & value
    self._write_register(_GYRO_CONFIG_0_REGISTER, masked_value | rng)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def gyro_bandwidth(self):
    """ Switch the gyroscope bandwidth and return the new bandwidth.
        Default value: 32 Hz; see table 3-9 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_0_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00111000 & value

  @gyro_bandwidth.setter
  def gyro_bandwidth(self, bandwidth=GYRO_32HZ):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_0_REGISTER)
    masked_value = 0b00000111 & value
    self._write_register(_GYRO_CONFIG_0_REGISTER, masked_value | bandwidth)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def gyro_mode(self):
    """ Switch the gyroscope mode and return the new mode.
        Default value: Normal; see table 3-9 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_1_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00000111 & value

  @gyro_mode.setter
  def gyro_mode(self, mode=GYRO_NORMAL_MODE):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_GYRO_CONFIG_1_REGISTER)
    masked_value = 0b00000000 & value
    self._write_register(_GYRO_CONFIG_1_REGISTER, masked_value | mode)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def magnet_rate(self):
    """ Switch the magnetometer data output rate and return the new rate.
        Default value: 20Hz; see table 3-10 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00000111 & value

  @magnet_rate.setter
  def magnet_rate(self, rate=MAGNET_20HZ):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    masked_value = 0b01111000 & value
    self._write_register(_MAGNET_CONFIG_REGISTER, masked_value | rate)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def magnet_operation_mode(self):
    """ Switch the magnetometer operation mode and return the new mode.
        Default value: Regular; see table 3-10 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b00011000 & value

  @magnet_operation_mode.setter
  def magnet_operation_mode(self, mode=MAGNET_REGULAR_MODE):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    masked_value = 0b01100111 & value
    self._write_register(_MAGNET_CONFIG_REGISTER, masked_value | mode)
    self._write_register(_PAGE_REGISTER, 0x00)

  @property
  def magnet_mode(self):
    """ Switch the magnetometer power mode and return the new mode.
        Default value: Forced; see table 3-10 in the datasheet.
    """
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    self._write_register(_PAGE_REGISTER, 0x00)
    return 0b01100000 & value

  @magnet_mode.setter
  def magnet_mode(self, mode=MAGNET_FORCEMODE_MODE):
    if self.mode in [0x08, 0x09, 0x0A, 0x0B, 0x0C]:
      raise RuntimeError("Mode must not be a fusion mode")
    self._write_register(_PAGE_REGISTER, 0x01)
    value = self._read_register(_MAGNET_CONFIG_REGISTER)
    masked_value = 0b00011111 & value
    self._write_register(_MAGNET_CONFIG_REGISTER, masked_value | mode)
    self._write_register(_PAGE_REGISTER, 0x00)

  def _write_register(self, register, value):
    raise NotImplementedError("Must be implemented.")

  def _read_register(self, register):
    raise NotImplementedError("Must be implemented.")

# ----------------------------------------------------------------------------
class BNO055(BNO055Base):
  """Driver for the BNO055 9DOF IMU sensor via I2C."""

  _temperature = _ReadOnlyUnaryStruct(0x34, "b")
  _acceleration = _ScaledReadOnlyStruct(0x08, "<hhh", 1 / 100)
  _magnetic = _ScaledReadOnlyStruct(0x0E, "<hhh", 1 / 16)
  _gyro = _ScaledReadOnlyStruct(0x14, "<hhh", 0.001090830782496456)
  _euler = _ScaledReadOnlyStruct(0x1A, "<hhh", 1 / 16)
  _quaternion = _ScaledReadOnlyStruct(0x20, "<hhhh", 1 / (1 << 14))
  _linear_acceleration = _ScaledReadOnlyStruct(0x28, "<hhh", 1 / 100)
  _gravity = _ScaledReadOnlyStruct(0x2E, "<hhh", 1 / 100)

  # Calibration offsets for the accelerometer, magnometer and gyroscope
  offsets_accelerometer = _ModeStruct(_OFFSET_ACCEL_REGISTER, "<hhh", CONFIG_MODE)
  offsets_magnetometer = _ModeStruct(_OFFSET_MAGNET_REGISTER, "<hhh", CONFIG_MODE)
  offsets_gyroscope = _ModeStruct(_OFFSET_GYRO_REGISTER, "<hhh", CONFIG_MODE)

  # Radius for accelerometer (cm?) and magnetometer (cm?)
  radius_accelerometer = _ModeStruct(_RADIUS_ACCEL_REGISTER, "<h", CONFIG_MODE)
  radius_magnetometer = _ModeStruct(_RADIUS_MAGNET_REGISTER, "<h", CONFIG_MODE)

  def __init__(self, i2c, address=ADDRESS_BNO055):
    self._i2c_addr = address
    super().__init__(i2c)

  def _write_register(self, register, value):
    buf = bytearray([register, value])
    with self.i2c_device as i2c:
      i2c.writeto(self._i2c_addr, buf)

  def _read_register(self, register):
    buf = bytearray([register, 0])
    with self.i2c_device as i2c:
      i2c.write_then_readinto(self._i2c_addr, buf, buf, out_end=1, in_start=1)
    return buf[1]

# ----------------------------------------------------------------------------
