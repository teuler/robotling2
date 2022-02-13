# ----------------------------------------------------------------------------
# dio.py
#
# Basic digital pin support
# (for rp2 micropython)
#
# The MIT License (MIT)
# Copyright (c) 2021-22 Thomas Euler
# 2021-02-28, v1.0
# 2022-01-03, v1.1, Nano RP2040 Connect added
# ----------------------------------------------------------------------------
import time
from micropython import const
from machine import Pin, PWM

# pylint: disable=bad-whitespace
__version__     = "0.1.1.0"

PULL_UP         = const(0)
PULL_DOWN       = const(1)
MAX_DUTY        = const(65536)
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class DigitalOut(object):
  """Basic digital output."""

  def __init__(self, pin, value=False):
    self._pin = Pin(pin, Pin.OUT)
    self._pin.value(value)

  def deinit(self):
    self._pin = None

  @property
  def value(self):
    return self._pin.value()

  @value.setter
  def value(self, value):
    self._pin.value(value)

  def on(self):
    self._pin.value(1)

  def off(self):
    self._pin.value(0)

# ----------------------------------------------------------------------------
class DigitalIn(object):
  """Basic digital input."""

  def __init__(self, pin, pull=None):
    if pull == PULL_UP:
      self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
    elif pull == PULL_DOWN:
      self._pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
    else:
      self._pin = Pin(pin, Pin.IN)

  def deinit(self):
    self._pin = None

  @property
  def value(self):
    return self._pin.value()

# ----------------------------------------------------------------------------
class PWMOut(object):
  """PWM output."""

  def __init__(self, pin, freq=50, duty=0, verbose=False, channel=-1):
    self._pin = PWM(Pin(pin))
    self._pin.freq(freq)
    self._pin.duty_u16(duty)
    self._verbose = verbose
    if self._verbose:
      self.__logFrequency()

  def deinit(self):
    self._pin.deinit()

  @property
  def duty_percent(self):
    """ duty in percent
    """
    return self._pin.duty_u16() /MAX_DUTY *100

  @duty_percent.setter
  def duty_percent(self, value):
    self._pin.duty_u16(int(min(max(0, value/100.0 *MAX_DUTY), MAX_DUTY)))

  @property
  def duty(self):
    """ duty as raw value
    """
    return self._pin.duty_u16()

  @duty.setter
  def duty(self, value):
    self._pin.duty_u16(int(value))

  @property
  def freq_Hz(self):
    """ frequency in [Hz]
    """
    return self._pin.freq()

  @freq_Hz.setter
  def freq_Hz(self, value):
    self._pin.freq(value)
    if self._verbose:
      self.__logFrequency()

  @property
  def max_duty(self):
    return MAX_DUTY

  @property
  def uses_rmt(self):
    return False

  def __logFrequency(self):
    print("PWM frequency is {0:.1f} kHz".format(self.freq_Hz/1000))

  def __setRMTDuty(self, value):
    pass

# ----------------------------------------------------------------------------
class Buzzer(object):
  """Buzzer."""

  def __init__(self, pin):
    self._buzz = PWMOut(pin)
    self._freq = 0
    self._mute = False

  @property
  def freq_Hz(self):
    return self._freq

  @freq_Hz.setter
  def freq_Hz(self, value):
    if value >= 10:
      self._buzz.freq_Hz = value
      self._freq = value

  @property
  def mute(self):
    return self._mute

  @mute.setter
  def mute(self, value):
    self._mute = value != 0

  def beep(self, freq=440, dur=100):
    if not self._mute:
      self.freq_Hz = freq
      self._buzz.duty_percent = 10
      time.sleep_ms(dur)
      self._buzz.duty_percent = 0
      self.freq_Hz = 0

  def warn(self):
    self.beep(110, 250)

  def deinit(self):
    self._buzz.deinit()

# ----------------------------------------------------------------------------
