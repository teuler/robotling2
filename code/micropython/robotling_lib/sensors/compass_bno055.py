# ----------------------------------------------------------------------------
# compass_bno055.py
# Compass based on BNO055 9-DoF MNU driver
#
# The MIT License (MIT)
# Copyright (c) 2018 Thomas Euler
# 2020-09-20, v1
# ----------------------------------------------------------------------------
from math import radians
from robotling_lib.misc.helpers import timed_function
from robotling_lib.sensors.sensor_base import SensorBase
from robotling_lib.driver.bno055 import BNO055, ADDRESS_BNO055
import robotling_lib.misc.ansi_color as ansi
import robotling_lib.robotling_board as rb

__version__ = "0.1.0.0"
CHIP_NAME   = "BNO055"

# ----------------------------------------------------------------------------
class Compass(SensorBase):
  """Compass class that uses the 9-DoF MNU BNO055 breakout."""

  def __init__(self, i2c):
    """ Requires already initialized I2C bus instance.
    """
    self._i2c = i2c
    self._BNO055 = None
    self._isReady = False
    super().__init__(None, 0)

    addrList = self._i2c.deviceAddrList
    if (ADDRESS_BNO055 in addrList):
      # Initialize
      try:
        self._BNO055 = BNO055(i2c)
        self._version = 1
        self._type = "Compass w/ tilt-compensation"
        self._isReady = True
      except RuntimeError:
        pass

    c = ansi.GREEN if self._isReady else ansi.RED
    cn = "{0}_v{1}".format(CHIP_NAME, self._version)
    print(c +"[{0:>12}] {1:35} ({2}): {3}"
          .format(cn, self._type, __version__,
                  "ok" if self._isReady else "FAILED") +ansi.BLACK)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def get_heading(self, tilt=False, calib=False, hires=True):
    """ Returns heading with or w/o tilt compensation and/or calibration,
        if available.
        NOTE: The BNO055 has built-in tilt compensation and is pre-calibra-
        ted, therefore the parameters `tilt` and `calib` are only for
        compatibility reasons and have no effect; `hires` is ignored.
    """
    if not self._isReady:
      return rb.RBL_ERR_DEVICE_NOT_READY
    return self._BNO055.euler[0]

  #@timed_function
  def get_heading_3d(self, calib=False):
    """ Returns heading, pitch and roll in [°] with or w/o calibration,
        if available.
        NOTE: The BNO055 has built-in tilt compensation and is pre-calibra-
        ted, therefore the parameter `calib` exists only for compatibility
        reasons and has no effect.
    """
    if not self._isReady:
      return (rb.RBL_ERR_DEVICE_NOT_READY, 0, 0, 0)
    hd, pit, rol = self._BNO055.euler
    return (rb.RBL_OK, hd, pit, rol)

  def get_pitch_roll(self, radians=False):
    """ Returns error code, pitch and roll in [°] as a tuple
    """
    if not self._isReady:
      return  (rb.RBL_ERR_DEVICE_NOT_READY, 0, 0)
    hd, pit, rol = self._BNO055.euler
    if radians:
      return (rb.RBL_OK, -1, radians(pit), radians(rol))
    else:
      return (rb.RBL_OK, -1, pit, rol)

  @property
  def is_ready(self):
    return self._isReady

  @property
  def channel_count(self):
    return CHAN_COUNT

# ----------------------------------------------------------------------------
