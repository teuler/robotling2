# ----------------------------------------------------------------------------
# board_rp2.py
# Hardware specific pin definitions.
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-02-28, v1
# ----------------------------------------------------------------------------
from micropython import const

__version__ = "0.1.0.0"

# ----------------------------------------------------------------------------
# Adafruit Huzzah32
# (USB connector down, from the top)
#
# pylint: disable=bad-whitespace
# Left column:
D0   = const(0)   #  1, I2C0_SDA, SPI0_RX,  UART0_TX
D1   = const(1)   #  2, I2C0_SCL, SPI0_CSn, UART0_RX

D2   = const(2)   #  4, I2C1_SDA, SPI0_SCK
D3   = const(3)   #  5, I2C1_SCL, SPI0_TX
D4   = const(4)   #  6, I2C0_SDA, SPI0_RX,  UART1_TX
D5   = const(5)   #  7, I2C0_SCL, SPI0_CSn, UART1_RX

D6   = const(6)   #  9, I2C1_SDA, SPI0_SCK
D7   = const(7)   # 10, I2C1_SCL, SPI0_TX
D8   = const(8)   # 11, I2C0_SDA, SPI1_RX,  UART1_TX
D9   = const(9)   # 12, I2C0_SCL, SPI1_CSn, UART1_RX

D10  = const(10)  # 14, I2C1_SDA, SPI1_SCK
D11  = const(11)  # 15, I2C1_SCL, SPI1_TX
D12  = const(12)  # 16, I2C0_SDA, SPI1_RX,  UART0_TX
D13  = const(13)  # 17, I2C0_SCL, SPI1_CSn, UART0_RX

D14  = const(14)  # 19, I2C1_SDA, SPI1_SCK
D15  = const(15)  # 20, I2C1_SCL, SPI1_TX

# Right column:
D28  = const(28)  # 34, ADC2

D27  = const(27)  # 32, ADC1, I2C0_SCL
D26  = const(26)  # 31, ADC0, I2C0_SDA

D22  = const(22)  # 29

D21  = const(21)  # 27, I2C0_SCL
D20  = const(20)  # 26, I2C0_SDA
D19  = const(19)  # 25, SPI0_TX,  I2C1_SCL
D18  = const(18)  # 24, SPI0_SCK, I2C1_SDA

D17  = const(17)  # 22, SPI0_CSn, I2C0_SCL, UART0_RX
D16  = const(16)  # 21, SPI0_RX,  I2C0_SDA, UART0_TX

# Special pins
LED  = const(25)  # green onboard LED
VBUS = const(24)  # VBUS sense, high=USB power connected
BAT  = const(29)  # ADC3 measuring VSYS/3
# pylint: enable=bad-whitespace

# Special functions
def voltage_V():
  from machine import ADC
  return ADC(3).read_u16() /65535 *3

def core_temperature_deg():
  from machine import ADC, CORE_TEMP
  val = ADC(CORE_TEMP).read_u16()
  return 27 -(val *3.3 /65535 -0.706) /0.001721

def is_vbus_present():
  from machine import Pin
  return Pin(board.VBUS, Pin.IN).value()


# ----------------------------------------------------------------------------
