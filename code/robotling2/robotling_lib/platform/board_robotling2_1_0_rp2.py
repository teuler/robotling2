# ----------------------------------------------------------------------------
# board_robotling2_1_0_rp2.py
# Pins and devices on `robotling2" board, version 1.0
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-02-28, v1
# ----------------------------------------------------------------------------
from micropython import const
import robotling_lib.platform.rp2.board_rp2 as board

# pylint: disable=bad-whitespace
'''
# SPI -----------------
SCK        = board.SCK
MOSI       = board.MOSI
MISO       = board.MISO
CS_ADC     = board.D4
CS_ADC1    = board.D26
CS_ADC2    = board.D25

# I2C -----------------
SCL        = board.SCL
SDA        = board.SDA
D_I2C      = board.D14

# UART  ---------------
TX         = board.TX
RX         = board.RX
BAUD       = 38400

# DIO -----------------
BLUE_LED   = board.D32      # -> also DIO3
NEOPIX     = board.D15      # -> Neopixel connector
DIO0       = board.D27
DIO1       = board.LED
DIO2       = board.D33
DIO3       = board.D32

# Other ---------------
ENAB_5V    = board.D16
RED_LED    = board.LED
ADC_BAT    = board.BAT

# Note 1: The ESP32 MicroPython port currently supports only one frequency
# for all PWM objects. Servos usually expect 50 Hz, but to run the DC motors
# somewhat smoother, a higher frequency can be tested
# Note 2: DIO uses now the RMT feature of the ESP32, which offers an
# alternative to the standard PWM with more flexible frequencies
SERVO_FRQ  = 50
MOTOR_FRQ  = SERVO_FRQ
MOTOR_A_CH = 0
MOTOR_B_CH = 1
'''
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
