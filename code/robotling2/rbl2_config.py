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
SRV_RANGE_US   = [(1010, 1810), (1100, 1900), (1191, 1625)]
SRV_RANGE_DEG  = [(-40, 40), (-40, 40), (-20, 20)]
SRV_ID         = bytearray([0,1,2])
SRV_PIN        = bytearray([board.D21, board.D10, board.D2])

COL_TXT_LO     = const(57351)  #0xffff
COL_TXT_HI     = const(40965)  #0x20ff
COL_TXT_RED    = const(248)
COL_BKG_LO     = const(0)      #0x22db
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
