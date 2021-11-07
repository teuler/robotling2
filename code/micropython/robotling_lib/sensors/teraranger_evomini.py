# ----------------------------------------------------------------------------
# teraranger_evomini.py
# Class for TeraRanger Evo Mini 4-pixel distance sensor
#
# The MIT License (MIT)
# Copyright (c) 2020 Thomas Euler
# 2020-08-08, v1
# 2020-12-20, v1.1, More robust managment of incoming data
# 2021-03-14, v1.2, Compatibility w/ rp2
# 2021-03-14, v1.3, Instead of counting invalid readings, give the time when
#                   the last valid measurement was taken
# ----------------------------------------------------------------------------
import array
from micropython import const
import robotling_lib.misc.ansi_color as ansi
from robotling_lib.misc.helpers import timed_function

try:
  import struct
except ImportError:
  import ustruct as struct

from robotling_lib.platform.platform import platform as pf
if pf.languageID == pf.LNG_MICROPYTHON:
  if pf.ID == pf.ENV_MPY_RP2:
    from machine import UART
  else:
    from robotling_lib.platform.esp32.busio import UART
  from time import sleep_ms, ticks_ms
  import select
elif pf.languageID == pf.LNG_CIRCUITPYTHON:
  from robotling_lib.platform.circuitpython.busio import UART
  from robotling_lib.platform.circuitpython.time import sleep_ms
else:
  print("ERROR: No matching hardware libraries in `platform`.")

# pylint: disable=bad-whitespace
__version__ = "0.1.3.0"

CHIP_NAME   = "tera_evomini"
CHAN_COUNT  = const(4)
# pylint: enavble=bad-whitespace

# pylint: disable=bad-whitespace
# User facing constants/module globals.
TERA_POLL_WAIT_MS   = const(5)

# Internal constants and register values:
_TERA_BAUD          = 115200
_TERA_CMD_WAIT_MS   = const(10)
_TERA_START_CHR     = b'T'
_TERA_OUT_MODE_TEXT = bytearray([0x00, 0x11, 0x01, 0x45])
_TERA_OUT_MODE_BIN  = bytearray([0x00, 0x11, 0x02, 0x4C])
_TERA_PIX_MODE_1    = bytearray([0x00, 0x21, 0x01, 0xBC])
_TERA_PIX_MODE_2    = bytearray([0x00, 0x21, 0x03, 0xB2])
_TERA_PIX_MODE_4    = bytearray([0x00, 0x21, 0x02, 0xB5])
_TERA_RANGE_SHORT   = bytearray([0x00, 0x61, 0x01, 0xE7])
_TERA_RANGE_LONG    = bytearray([0x00, 0x61, 0x03, 0xE9])
# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
class TeraRangerEvoMini:
  """Driver for the TeraRanger Evo Mini 4-pixel distance sensor."""
  # pylint: disable=bad-whitespace
  # User facing constants/module globals.
  TERA_DIST_NEG_INF   = const(0x0000)
  TERA_DIST_POS_INF   = const(0xFFFF)
  TERA_DIST_INVALID   = const(0x0001)
  # pylint: enable=bad-whitespace

  def __init__(self, id, tx, rx, nPix=4, short=True):
    """ Requires pins and channel for unused UART
    """
    self._uart = UART(id, tx=tx, rx=rx, baudrate=_TERA_BAUD)
    self._nPix = nPix
    self._short = short
    self._nInvalData = 0

    # Set pixel mode and prepare buffer
    if self._nPix == 4:
      self._uart.write(_TERA_PIX_MODE_4)
    elif self._nPix == 2:
      self._uart.write(_TERA_PIX_MODE_2)
    else:
      self._nPix = 1
      self._uart.write(_TERA_PIX_MODE_1)
    sleep_ms(_TERA_CMD_WAIT_MS)
    self._nBufExp = self._nPix*2 +2
    self._dist = array.array("i", [0]*self._nPix)
    self._tLast = array.array("I", [0]*self._nPix)
    self._sInBuf = b""

    # Set binary mode for results
    self._uart.write(_TERA_OUT_MODE_BIN)
    sleep_ms(_TERA_CMD_WAIT_MS)

    # Set distance mode
    if self._short:
      self._uart.write(_TERA_RANGE_SHORT)
    else:
      self._uart.write(_TERA_RANGE_LONG)
    sleep_ms(_TERA_CMD_WAIT_MS)

    # Prepare polling construct, if available
    self._poll = None
    if pf.ID in [pf.ENV_ESP32_UPY, pf.ENV_MPY_RP2]:
      self._poll = select.poll()
      self._poll.register(self._uart, select.POLLIN)

    self._isReady = True
    c = ansi.GREEN if self._isReady else ansi.RED
    print(c +"[{0:>12}] {1:35} ({2}): {3}"
          .format(CHIP_NAME, "TeraRanger Evo Mini", __version__,
                  "ok" if self._isReady else "NOT FOUND") +ansi.BLACK)

  def __deinit__(self):
    if self._uart is not None:
      self._uart.deinit()
      self._isReady == False

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def update(self, raw=True):
    """ Update distance reading(s)
    """
    if self._uart is not None:
      # Check if any new data arrived ...
      if self._poll:
        self._poll.poll(TERA_POLL_WAIT_MS)
      if self._uart.any() == 0:
        # No new data
        return

      # Data are waiting; add them to the buffer
      nExp = self._nBufExp
      sBuf = bytes()
      '''
      sBuf = self._uart.readline()
      if not sBuf:
        # UART returns None?!
        self.__logError("UART returns `None`")
        return
      '''
      while self._uart.any() > 0:
        sBuf += self._uart.read(1)

      self._sInBuf += bytearray(sBuf)
      if len(self._sInBuf) < nExp:
        # (Still) too few characters for a complete message
        return

      # Should contain a complete reading
      tmp = self._sInBuf.split(_TERA_START_CHR)
      nDt = len(tmp)
      if nDt == 0:
        self._nInvalData += 1
        return

      if len(tmp[nDt -1]) < nExp -1:
        # Incomplete dataset at the end; keep characters
        self._sInBuf = _TERA_START_CHR +tmp[nDt -1]
        iDt = nDt -2
        if len(tmp[iDt]) < nExp -1:
          self._nInvalData += 1
          return
      else:
        # Ends with a complete dataset or is only one dataset
        self._sInBuf = bytes()
        iDt = nDt -1

      # Decode reading
      self._nInvalData = 0
      np = self._nPix
      if np == 4:
        d = struct.unpack_from('>HHHH', tmp[iDt][0:8]) #buf[1:9])
      elif np == 2:
        d = struct.unpack_from('>HH', tmp[iDt][0:4]) #buf[1:5])
      else:
        d = struct.unpack_from('>H',  tmp[iDt][0:2]) #buf[1:3])
      if raw:
        # Just copy new values to `dist`
        self._dist = d
      else:
        # Check if values are valid and keep track of last valid reading
        t = ticks_ms()
        for iv,v in enumerate(d):
          if v is not TERA_DIST_INVALID:
            self._dist[iv] = v
            self._tLast[iv] = t

  @property
  def distances(self):
    return self._dist

  @property
  def last_valid_ms(self):
    return self._tLast

  def __logError(self, msg):
    print(ansi.RED + "{0}|Error: {1}".format(CHIP_NAME, msg) +ansi.BLACK)

# ----------------------------------------------------------------------------
