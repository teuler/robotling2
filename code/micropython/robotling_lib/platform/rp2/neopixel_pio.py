# ----------------------------------------------------------------------------
# neopixel_pio.py
#
# Basic NeoPixel support
# (for micropython on a rp2 via PIO)
#
# The MIT License (MIT)
# Copyright (c) 2021-22 Thomas Euler
# 2021-03-13, v1.0, first version
# 2022-01-03, v1.1, version using `neopixel` module added
# ----------------------------------------------------------------------------
import rp2
import array, time
from machine import Pin

# pylint: disable=bad-whitespace
__version__    = "0.1.1.0"
FREQ           = 8_000_000
# pylint: enabled=bad-whitespace

# ----------------------------------------------------------------------------
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

# ----------------------------------------------------------------------------
class NeoPixel(object):
  """Basic NeoPixel class"""

  def __init__(self, pin, nNPs=1):
    """ Requires a pin index and the number of NeoPixels
    """
    self._numLEDs = nNPs
    self._pin = pin
    self._brightness = 0.1
    self._data = array.array("I", [0 for _ in range(nNPs)])

    # Create the StateMachine with the WS2812 program and start it; it will
    # still wait for data
    self._SM = rp2.StateMachine(0, ws2812, freq=FREQ, sideset_base=Pin(pin))
    self._SM.active(1)

  def set(self, rgb, iNP=0, show=False):
    """ Takes an RGB value as a tupple for the NeoPixel with the index `iNP`,
        update all NeoPixels if `show`==True
    """
    if iNP >= 0 and iNP < self._numLEDs:
      self._data[iNP] = (rgb[1] << 16) +(rgb[0] << 8) +rgb[2]
    if show:
      self.show()

  def show(self):
    """ Display new pixel values
    """
    dta = self._data
    out = array.array("I", [0]*self._numLEDs)
    brg = self._brightness
    for i, c in enumerate(dta):
      r = int(((c >> 8) & 0xFF) *brg)
      g = int(((c >> 16) & 0xFF) *brg)
      b = int((c & 0xFF) *brg)
      out[i] = (g<<16) +(r<<8) +b
    self._SM.put(out, 8)
    time.sleep_ms(10)

  @property
  def brightness(self):
    return self._brightness

  @brightness.setter
  def brightness(self, value):
    self._brightness = min(max(value, 0), 1)

# ----------------------------------------------------------------------------
