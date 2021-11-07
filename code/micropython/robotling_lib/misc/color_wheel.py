# ----------------------------------------------------------------------------
# color_wheel.py
#
# The MIT License (MIT)
# Copyright (c) 2020 Thomas Euler
# 2020-12-20, v1
# ----------------------------------------------------------------------------
def getColorFromWheel(iWheel):
  """ Get an RGB color from a wheel-like color representation
  """
  iWheel = iWheel % 255
  if iWheel < 85:
    return (255 -iWheel*3, 0, iWheel*3)
  elif iWheel < 170:
    iWheel -= 85
    return (0, iWheel*3, 255 -iWheel*3)
  else:
    iWheel -= 170
    return (iWheel*3, 255 -iWheel*3, 0)

# ----------------------------------------------------------------------------
