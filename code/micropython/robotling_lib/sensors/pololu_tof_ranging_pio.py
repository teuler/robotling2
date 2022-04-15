# ----------------------------------------------------------------------------
# pololu_tof_ranging.py
# Pololu time-of-flight distance ranging sensors w/ PWM output
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-05-02, v1
# 2021-02-12, v1.1
# 2022-04-08, v1.2, improve sensor performance
# 2022-04-14, v1.3, alternate PIO version
# ----------------------------------------------------------------------------
import rp2
from micropython import const
from machine import Pin, freq
from rp2 import PIO, StateMachine, asm_pio
from robotling_lib.sensors.sensor_base import SensorBase
import robotling_lib.misc.ansi_color as ansi
from robotling_lib.misc.helpers import timed_function

# pylint: disable=bad-whitespace
__version__    = "0.1.3.0"
CHIP_NAME      = "IRS16A"
TIMEOUT_US     = const(20_000)
N_REREADS      = const(1)
N_AVG          = const(1)
ERR_TIMEOUT    = const(-1)
# pylint: enable=bad-whitespace

@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=32)
def pulse():
  wrap_target()
  set(x, 0)
  wait(0, pin, 0)         # Wait for pin to go low
  wait(1, pin, 0)         # Low to high transition
  label('low_high')
  jmp(x_dec, 'next') [1]  # unconditional
  label('next')
  jmp(pin, 'low_high')    # while pin is high
  in_(x, 32)              # Auto push: SM stalls if FIFO full
  wrap()
    
# ----------------------------------------------------------------------------
class PololuTOFRangingSensor(SensorBase):
  """Class for pulse-width Pololu time-of-flight ranging sensor."""

  def __init__(self, pin, pio_ID):
    super().__init__(driver=None, chan=1)
    assert freq() == 125_000_000, "CPU frequency must be 125 MHz"
    assert pio_ID in range(8), "PIO ID must be 0..7"
    self._pioID = pio_ID
    self._pin = Pin(pin, Pin.IN) #, Pin.PULL_UP)
    self.sm0 = rp2.StateMachine(
        pio_ID, pulse,
        in_base=self._pin, jmp_pin=self._pin
      )
    self.sm0.active(1)
    self._type = "time-of-flight range"
    self._isReady = True
    c = ansi.GREEN if self._isReady else ansi.RED
    print(c +"[{0:>12}] {1:35} ({2}): {3}"
          .format(CHIP_NAME, "Pololu time-of-flight w/PIO", __version__,
                  "ok" if self._isReady else "NOT FOUND") +ansi.BLACK)
  
  def deinit(self):
    self.sm0.active(0)
      
  @property
  def range_raw(self):
    # Clock is 125MHz. 3 cycles per iteration, so unit is 24.0ns
    # -> scale to us
    tp = self.sm0.get()
    return (1 + (tp ^ 0xffffffff)) *24e-6 *1000

  @micropython.native
  @property
  def range_cm(self):
    tavg = self.range_raw
    return 0.75 *(tavg -1000) /10
  
# ----------------------------------------------------------------------------
