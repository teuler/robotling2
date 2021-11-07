# ----------------------------------------------------------------------------
# minigui.py
# ...
#
# The MIT License (MIT)
# Copyright (c) 2021 Thomas Euler
# 2021-01-01, v1
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ----------------------------------------------------------------------------
import array

_display = None

# ----------------------------------------------------------------------------
class Widget(object):
  """Widget base"""

  def __init__(self, rect):
    # Initialize
    global _display
    self._w, self._h = _display.size
    self._rCanv = array.array("i", [rect[0], rect[1], rect[2], rect[3]])
    self._elems = []
    self._firstDraw = True

  def undraw(self):
    # Remove all elements from the display's group
    global _display
    for e in self._elems:
      _display.group.remove(e)
    self._elems = []

  @staticmethod
  def init(display):
    global _display
    _display = display

# ----------------------------------------------------------------------------
class WidgetBar(Widget):
  """Bar widget"""

  def __init__(self, rect, minmax, unit="n/a", label=""):
    # Initialize
    super().__init__(rect)
    self._min, self._max = minmax
    self._unit = unit
    self._label = label

  def draw(self, val, alt_str=None, alt_val=None):
    global _display
    self.undraw()
    x, y, dx, dy = self._rCanv
    dyf = _display.font_height
    dx1 = dx //3 -1
    dy1 = max(int(min((val -self._min) /(self._max -self._min), 1) *(dy-2)), 1)
    x1 = x +2*dx //3
    y1 = y +1 +(dy-2 -dy1)
    self._elems.append(_display.rect(x1, y1, dx1, dy1, fill=2, outline=3))
    s = alt_str if alt_str else "{0:.0f}{1}".format(val, self._unit)
    if self._firstDraw:
      _display.rect(x, y, dx-1, dy-1, fill=1, outline=0)
      _display.rect(x1, y+1, dx1, dy-2, outline=2)
      #self._unitStr = _display.text(self._unit, x+3, y+1 +dyf, 3, 1)
      self._valStr = _display.text("-"*6, x+3, y+1, 3, 1)
      self._firstDraw = False
    else:
      self._valStr.text = s
      #self._unitStr.text = str(alt_val) if alt_val else self._unit

# ----------------------------------------------------------------------------
class WidgetBattery(Widget):
  """Battery widget"""

  def __init__(self, rect, minmax, unit="n/a", label=""):
    # Initialize
    super().__init__(rect)
    self._min, self._max = minmax
    self._unit = unit
    self._label = label

  def draw(self, val, alt_str=None):
    global _display
    self.undraw()
    x, y, dx, dy = self._rCanv
    dx1 = max(int(min((val -self._min) /(self._max -self._min), 1) *(dx-2)), 1)
    s = alt_str if alt_str else "{0:.1f}{1}".format(val, self._unit)
    s = self._label +s
    self._elems.append(_display.rect(x+1, y+1, dx1, dy-2, fill=2))
    self._elems.append(_display.text(s, x+3, y+1, 3, 1, btransparent=True))
    if self._firstDraw:
      _display.rect(x, y, dx-1, dy-1, fill=1, outline=0)
      self._firstDraw = False

# ----------------------------------------------------------------------------
class WidgetHeartbeat(Widget):
  """Heartbeat widget"""

  def __init__(self, rect):
    # Initialize
    super().__init__(rect)
    self._state = 0

  def draw(self):
    global _display
    self.undraw()
    x, y, dx, dy = self._rCanv
    r = dy //6 *self._state
    self._elems.append(_display.circle(x +dx//2, y +dy//2, r, outline=2))
    self._state = self._state +1 if self._state < 3 else 0

# ----------------------------------------------------------------------------
