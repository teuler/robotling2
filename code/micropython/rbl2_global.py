# ----------------------------------------------------------------------------
# rbl2_global.py
#
# Global definitions
#
# The MIT License (MIT)
# Copyright (c) 2021-2022 Thomas Euler
# 2021-03-03, v1.0
# ----------------------------------------------------------------------------
from micropython import const
import robotling_lib.misc.ansi_color as ansi

# pylint: disable=bad-whitespace
# General
VERBOSE             = const(0)

# States
STATE_NONE          = const(0)
STATE_IDLE          = const(1)
STATE_STOPPING      = const(2)
STATE_WALKING       = const(3)
STATE_REVERSING     = const(4)
STATE_TURNING       = const(5)
STATE_POWERING_DOWN = const(6)
STATE_OFF           = const(7)
# ...
STATE_STRS          = ["None", "Idle",
                       "Stopping", "Walking", "Backing up", "Turning",
                       "Powering down", "Off"]
# Commands
CMD_NONE            = const(0)
CMD_STOP            = const(1)
CMD_MOVE            = const(2)
CMD_POWER_DOWN      = const(3)
# ...

# pylint: enable=bad-whitespace

# ----------------------------------------------------------------------------
def toLog(sMsg, sTopic="", errC=0, green=False, color=None, verbose=True):
  """ Print message to history
  """
  if not verbose:
    return
  c = ""
  if errC == 0:
    s = "INFO" if len(sTopic) == 0 else sTopic
    if green:
      c = ansi.GREEN
  elif errC > 0:
    s = "WARNING"
    c = ansi.CYAN
  else:
    s = "ERROR"
    c = ansi.RED
  if color:
    c = color
  print(c +"[{0:>12}] {1:35}".format(s, sMsg) +ansi.BLACK)

# ----------------------------------------------------------------------------
