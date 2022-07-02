# ----------------------------------------------------------------------------
# rbl2_config.py
#
# Configuration and global definitions
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-03-03, v1.0
# 2021-04-05, v1.1 - D21 instead of D9, because the latter shows irrative
#                    behaviour when used together with picodisplay
# 2022-02-12, v1.2 - More sensors allowed, constants for sensor port pins
# 2022-04-08, v1.3 - small fixes for MicroPython 1.18
# 2022-07-02, v1.4 - small fixes for new Pico Display API (MPy 1.19)
# ----------------------------------------------------------------------------
from micropython import const
from robotling_lib.platform.rp2 import board_rp2 as board

# pylint: disable=bad-whitespace
# Firmware info
RBL2_VERSION   = 1.4
RBL2_INFO      = "Robotling2"

# Control how hardware is kept updated
HW_CORE        = const(0)   # 1=hardware update runs on second core
APPROX_SPIN_MS = const(5)   # core==0, approx. duration of hardware update
MIN_UPDATE_MS  = const(20)  # core==0, minimal time between hardware updates
PULSE_STEPS    = const(10)  # Number of steps for Pixel/RGB pulsing

# Sensor port pins (idenfiers on PCB)
SPO_D0         = board.D3
SPO_AI2        = board.D28
SPO_AI0        = board.D26
SPO_AI1        = board.D27
SPO_D1         = board.D22
SPO_RX         = board.D5
SPO_SC         = board.D1
SPO_TX         = board.D4
SPO_SD         = board.D0

# Servo-related definitions
SRV_RANGE_US   = [(1110, 1810), (1100, 1800), (1291, 1565)]
SRV_RANGE_DEG  = [(-40, 40), (-40, 40), (-20, 20)]
SRV_ID         = bytearray([0,1,2])
SRV_PIN        = bytearray([board.D21, board.D10, board.D2])

COL_TXT_LO     = ( 20,  64,  20)
COL_TXT        = ( 96, 128,  96)
COL_TXT_HI     = ( 40, 255,  40)
COL_TXT_OTHER  = ( 20, 128,  20)
COL_TXT_WARN   = (256, 128,   0)
COL_BKG_HI     = ( 10,  40,  10)
COL_BKG_LO     = (  0,   0,   0)

PIMORONI_PICO_DISPLAY = const(1)

# Devices
# Value(s): "tof_pwm", "display"
DEVICES        = ["tof_pwm", "display"]
DISPLAY_TYPE   = PIMORONI_PICO_DISPLAY

# Pico Display-related definitions
# (as GP pin)
LED_R_PIN      = const(6)
LED_G_PIN      = const(7)
LED_B_PIN      = const(8)
BTN_A_PIN      = const(12)
BTN_B_PIN      = const(13)
BTN_X_PIN      = const(14)
BTN_Y_PIN      = const(15)

# Sensor types
STY_NONE       = const(0)
STY_TOF        = const(1)
STY_EVOMINI    = const(2)

# Pololu tof distance sensor array w/ PWM output
TOFPWM_USE_PIO = False
TOFPWM_PIOS    = [0, 1, 2]
TOFPWM_PINS    = [SPO_D0, SPO_RX, SPO_TX]
TOFPWM_MIN_MM  = const(10)
TOFPWM_MAX_MM  = const(200)
TOFPWM_LEFT    = const(0)
TOFPWM_CENTER  = const(1)
TOFPWM_RIGHT   = const(2)

# TeraRanger EvoMini (for "evo_mini" in `DEVICES`)
EVOMINI_UART   = const(1)
EVOMINI_TX     = board.D4
EVOMINI_RX     = board.D5
EVOMINI_MIN_MM = const(10)
EVOMINI_MAX_MM = const(500)
EVOMINI_R_LOW  = const(0)
EVOMINI_L_HIGH = const(1)
EVOMINI_L_LOW  = const(2)
EVOMINI_R_HIGH = const(3)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
