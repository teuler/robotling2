# ----------------------------------------------------------------------------
# camera_thermal.py
# ...
#
# The MIT License (MIT)
# Copyright (c) 2019 Thomas Euler
# 2019-08-01, v1
# 2019-12-15, v1.1
# 2020-08-21, v1.2 Now only valid blobs are returned; now uses a Python blob
#                  module if `blob` is not in the firmware
#
# Known issues with `blob`:
# - Only mode=0 seems not to crash the ESP32 ...
# - The "probability" for a blob can exceed 1.0 (???)
#
# ----------------------------------------------------------------------------
import time
try:
  import robotling_lib.misc.blob_ulab2 as blob
  BLOB_SUPPORT = 0
except ImportError:
  try:
    import robotling_lib.misc.blob_ulab as blob
    BLOB_SUPPORT = 1
  except ImportError:
    import robotling_lib.misc.blob as blob
    BLOB_SUPPORT = 2

import robotling_lib.misc.ansi_color as ansi
from robotling_lib.sensors.sensor_base import CameraBase

__version__ = "0.1.2.0"

# ----------------------------------------------------------------------------
class Camera(CameraBase):
  """Camera class for the AMG88XX GRID-Eye IR 8x8 thermal camera."""

  def __init__(self, driver):
    super().__init__(driver)
    self._type = "thermal camera (8x8)"
    if driver.isReady:
      # Initialize
      self._dxy = self.resolution
      self._params = None
      self._img64x1 = []
      self._blobList = []
      self._dtMean = 0

    c = ansi.GREEN if driver.isReady else ansi.RED
    s = "{0} ({1})".format(self._type, ["C++", "ulab", "Python"][BLOB_SUPPORT])
    print(c +"[{0:>12}] {1:35} ({2}): {3}"
          .format(driver.name, s, __version__,
                  "ok" if driver.isReady else "FAILED") +ansi.BLACK)

  def detectBlobs(self, kernel=None, nsd=1.0):
    """ Acquire image and detect blobs, using filter (`kernel`), and threshold
        for blob detection of `nsd` (in number of standard deviations)
    """
    self._img64x1 = []
    self._blobList = []
    if self._driver.isReady:
      self._img64x1 = list(self._driver.pixels_64x1)
      if kernel:
        self._img64x1 = blob.spatial_filter(self._img64x1, kernel, self._dxy)
      self._blobList = blob.find_blobs(self._img64x1, self._dxy, nsd)

  @property
  def blobsRaw(self):
    """ Return raw blob list
    """
    return self._blobList

  @property
  def imageLinear(self):
    """ Return current image as a 1D list
    """
    return self._img64x1

  def getBestBlob(self, minArea, minP):
    """ Return the (corrected) position of the best blob that meets the
        given criteria: minimal area `minArea` and probabilty >= `minP`
        (check known issues with `blob`; the "probability" can exceed 1.0 ...)
    """
    if len(self._blobList) > 0:
      area = self._blobList[0][0]
      prob = self._blobList[0][2]
      if area >= minArea and prob >= minP:
        # Return coordinates of that blob
        # (Note that the coordinates are adjusted here to match the view
        #  of the robot with the _AMG88XX mounted with the cable connector up)
        return (self._blobList[0][3] -self._dxy[0]/2,
                self._blobList[0][4] -self._dxy[1]/2)
    else:
      return None

# ----------------------------------------------------------------------------
