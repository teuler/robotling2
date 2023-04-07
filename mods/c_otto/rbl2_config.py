# ----------------------------------------------------------------------------
# rbl2_config.py
#
# Configuration and global definitions
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-03-03, v1.0
# 2021-04-05, v1.1 - D21 instead of D9, because the latter shows irrative
#                    behaviour when used together with picodisplay
# ----------------------------------------------------------------------------
from micropython import const
from robotling_lib.platform.rp2 import board_rp2 as board

# pylint: disable=bad-whitespace
# Firmware info
RBL2_VERSION   = 1
RBL2_INFO      = "Robotling2"

# Control how hardware is kept updated
HW_CORE        = const(0)   # 1=hardware update runs on second core
APPROX_SPIN_MS = const(5)   # core==0, approx. duration of hardware update
MIN_UPDATE_MS  = const(20)  # core==0, minimal time between hardware updates
PULSE_STEPS    = const(10)  # Number of steps for Pixel/RGB pulsing

# Servo-related definitions
SRV_RANGE_US   = [(1510, 1860), (1262, 1655), (1610, 1817)]
SRV_RANGE_DEG  = [(-40, 40), (-40, 40), (-20, 20)]
SRV_ID         = bytearray([0,1,2])
SRV_PIN        = bytearray([board.D7, board.D6, board.D21])

COL_TXT_LO     = const(40965)
COL_TXT        = const(57351)
COL_TXT_HI     = const(63951)
COL_TXT_OTHER  = const(14595)
COL_TXT_WARN   = const(248)
COL_BKG_LO     = const(0)

# Devices
DEVICES        = ["VL53L0x"]

# # TeraRanger EvoMini
# EVOMINI_UART   = const(1)
# EVOMINI_TX     = board.D4
# EVOMINI_RX     = board.D5
# EVOMINI_MIN_MM = const(10)
# EVOMINI_MAX_MM = const(500)
# EVOMINI_R_LOW  = const(0)
# EVOMINI_L_HIGH = const(1)
# EVOMINI_L_LOW  = const(2)
# EVOMINI_R_HIGH = const(3)
# 
# VL53L0X Time of flight sensor
TOFL_I2C       = const(0)
TOFL_SDA       = board.D0
TOFL_SCL       = board.D1
TOFL_SHUT_1    = board.D3
TOFL_SHUT_2    = board.D22
TOF_MAX_MM     = const(200)
TOF_MIN_MM     = const(80)

# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
