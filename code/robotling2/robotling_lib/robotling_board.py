# ----------------------------------------------------------------------------
# robotling_board.py
# Global definitions for robotling board.
#
# The MIT License (MIT)
# Copyright (c) 2018-21 Thomas Euler
# 2018-09-13, v1
# 2018-12-22, v1.1 - pins for M4 feather express added
# 2020-01-01, v1.2 - pins for hexapod robotling added
# 2020-08-08, v1.3 - pin/device assignments into separate files
# ----------------------------------------------------------------------------
from micropython import const
from robotling_lib.platform.platform import platform as pf
try:
  from robotling_board_version import BOARD_VER
except ImportError:
  BOARD_VER = 0

__version__ = "0.1.3.0"

SPI_FRQ    = const(4000000)
I2C_FRQ    = const(400000)

# I2C devices, maximal clock frequencies:
# AMG88XX (Infrared Array Sensor “Grid-EYE”)  <= 400 KHz
# VL6180X (Time of Flight distance sensor)    <= 400 KHz
# CMPS12  (Compass)                           <= 400 KHz
# LSM303  (Compass)                           100, 400 KHz
# LSM9DS0 (Compass)                           100, 400 KHz
# BNO055  (Compass)                           <= 400 KHz
# SSD1327 (Display)                           up to 800 KHz?

# ----------------------------------------------------------------------------
# Robotling/Hexapod board connections/pins
#
if pf.ID == pf.ENV_ESP32_UPY:
  # HUZZAH32 ESP32 board w/MicroPython
  if BOARD_VER == 100:
    from robotling_lib.platform.board_robotling_1_0_huzzah32 import *
  elif BOARD_VER >= 110 and BOARD_VER < 200:
    from robotling_lib.platform.board_robotling_1_3_huzzah32 import *
  elif BOARD_VER == 200:
    from robotling_lib.platform.board_robotling_2_0_huzzah32 import *

elif pf.ID == pf.ENV_ESP32_TINYPICO:
  # TinyPICO ESP32 board w/MicroPython
  from robotling_lib.platform.board_hexapod_0_41_tinypico import *

elif pf.ID == pf.ENV_CPY_SAM51:
  # SAM51 board w/CircuitPython
  from robotling_lib.platform.board_robotling_1_3_sam51 import *

elif pf.ID == pf.ENV_CPY_FEATHERS2:
  # ESP32s2 board w/CircuitPython
  if BOARD_VER == 042:
    from robotling_lib.platform.board_hexapod_0_42_featherS2 import *

elif pf.ID == pf.ENV_ESP32_S2:
  # ESP32s2 board w/MicroPython
  if BOARD_VER == 042:
    from robotling_lib.platform.board_hexapod_0_42_featherS2_mpy import *

else:
  # No fitting board found or wtong board version number
  assert False, "No fitting board found"

# ----------------------------------------------------------------------------
if pf.ID in [pf.ENV_ESP32_UPY, pf.ENV_ESP32_TINYPICO]:
  # The battery is connected to the pin via a voltage divider (1/2), and thus
  # an effective voltage range of up to 7.8V (ATTN_11DB, 3.9V); the resolution
  # is 12 bit (WITDH_12BIT, 4096 -1):
  # V = adc /(4096-1) *2 *3.9 *0.901919 = 0.001717522
  # (x2 because of voltage divider, x3.9 for selected range (ADC.ATTN_11DB)
  #  and x0.901919 as measured correction factor)
  def battery_convert(v):
    return v *0.001717522

elif pf.ID == pf.ENV_CPY_NRF52:
  # For 3.3V ADC range and 16-bit ADC resolution = 3000mV/65536
  # 150K + 150K voltage divider on VBAT => compensation factor 2.0
  def battery_convert(v):
    return v *3.3/65536 *2

else:
  def battery_convert(v):
    return 0

# ----------------------------------------------------------------------------
# Error codes
#
RBL_OK                      = const(0)
RBL_ERR_DEVICE_NOT_READY    = const(-1)
RBL_ERR_SPI                 = const(-2)
# ...

# ----------------------------------------------------------------------------
