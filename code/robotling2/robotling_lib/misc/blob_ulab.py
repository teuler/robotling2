#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# blob.py
# Function for blob detection in images
#
# The MIT License (MIT)
# Copyright (c) 2019 Thomas Euler
# 2020-08-21, v1.0 Analogous to the `blob.c` code with `ulab` support
#
# ---------------------------------------------------------------------
import math
import ulab as np
from ulab import numerical
from micropython import const
from robotling_lib.misc.helpers import timed_function

# pylint: disable=bad-whitespace
MAX_BLOBS          = const(5)
MAX_BLOB_FIELDS    = const(5)
xoffs              = np.array([-1, 1,  0, 0])
yoffs              = np.array([ 0, 0, -1, 1])
# pylint: enable=bad-whitespace

class blob_struct(object):
  def __init__(self, area=0, ID=0, prob=0, x=0, y=0):
    self.area = area
    self.ID = ID
    self.prob = prob
    self.x = x
    self.y = y

  @property
  def as_list(self):
    return [self.area, self.ID, self.prob, self.x, self.y]

  def copy(self, b):
    self.area = b.area
    self.ID = b.ID
    self.prob = b.prob
    self.x = b.x
    self.y = b.y

# ---------------------------------------------------------------------
def spatial_filter(img, kernel, dxy=None):
  """ Convolves `img` with `kernel` assuming a stride of 1. If `img` is linear,
     `dxy` needs to hold the dimensions of the image.
  """
  # Make sure that the image is 2D
  _img = np.array(img)
  if dxy is None:
    dx, dy = _img.shape()
    isInt = type(img[0:0])
    isFlat = False
  else:
    dx, dy = dxy
    if dx*dy != _img.size():
      raise TypeError("Dimensions do not match number of `img` elements")
    isInt = type(img[0])
    isFlat = True
  img2d = _img.reshape((dx, dy))

  # Check if kernel is a square matrix with an odd number of elements per row
  # and column
  krn = np.array(kernel)
  dk, dk2 = krn.shape()
  if dk != dk2 or dk % 2 == 0 or dk <= 1:
    raise TypeError("`kernel` is not a square 2D matrix or does not have an "
                    "odd number of row / column elements")

  # Make a padded copy of the image; pad with mean of image to reduce edge
  # effects
  padd = dk // 2
  img2dp = np.ones((dx +padd*2, dy +padd*2)) *numerical.mean(img2d)
  img2dp[padd:dx+padd,padd:dy+padd] = img2d
  imgRes = np.zeros(img2dp.shape())

  # Convolve padded image with kernel
  for x in range(0, dx):
    for y in range(0, dy):
      imgRes[x+padd,y+padd] = numerical.sum(img2dp[x:x+dk,y:y+dk] *krn[:,:])

  # Remove padding, flatten and restore value type if needed
  _img = imgRes[padd:dx+padd,padd:dy+padd]
  if isFlat:
    _img = _img.flatten()
  if isInt:
    _img = list(np.array(_img, dtype=np.int16))
  return _img

# ---------------------------------------------------------------------
@timed_function
def find_blobs_timed(img, dxy, nsd=1.0):
  return find_blobs(img, dxy, nsd)

def find_blobs(img, dxy, nsd=1.0):
  """ Detect continues area(s) ("blobs") with pixels above a certain
      threshold in an image. `img` contains the flattened image (1D),
      `dxy` image width and height, and `nsd` a factor to calculate the blob
      threshold from image mean and s.d. (thres = avg +sd *nsd).
  """
  # Initialize
  blobs = []
  for i in range(MAX_BLOBS):
    blobs.append(blob_struct())
  nBlobs = 0
  posList = []

  # Extract the parameters
  dx, dy = dxy
  n = dx*dy

  # Copy image data into a float array
  pImg = np.array(img)

  # Calculate mean and sd across (filtered) image to determine threshold
  avg = numerical.mean(pImg)
  sd = numerical.std(pImg)
  thres = avg +sd *nsd

  # Find blob(s) ...
  #
  # Mark all pixels above a threshold
  pPrb = (pImg -avg) /sd
  pMsk = np.array(pImg >= thres, dtype=np.uint8) *255
  nThres = int(numerical.sum(pMsk) /255)

  # Check if these above-threshold pixels represent continuous blobs
  nLeft = nThres
  iBlob = 0
  while nLeft > 0 and iBlob < MAX_BLOBS:
    # As long as unassigned mask pixels are left, find the next one using
    # `ulab.numerical.argmax()`, which returns the index of the (first)
    # hightest value, which should be 255
    iPix = numerical.argmax(pMsk)
    x = iPix % dx
    y = iPix //dx

    # Unassigned pixel found ...
    posList.append((x, y))
    pMsk[x +y*dx] = iBlob
    nFound = 1
    bx = float(x)
    by = float(y)
    bp = pPrb[x +y*dx]

    # Find all unassigned pixels in the neighborhood of this seed pixel
    while len(posList) > 0:
      x0, y0 = posList.pop()
      for k in range(4):
        x1 = x0 +xoffs[k]
        y1 = y0 +yoffs[k]
        if((x1 >= 0) and (x1 < dx) and
           (y1 >= 0) and (y1 < dy) and
           (pMsk[int(x1 +y1*dx)] == 255)):
          # Add new position from which to explore
          posList.append((x1, y1))
          pMsk[int(x1 +y1*dx)] = iBlob
          nFound += 1
          bx += float(x1)
          by += float(y1)
          bp += pPrb[int(x1 +y1*dx)]
    # Update number of unassigned pixels
    nLeft -= nFound

    # Store blob properties (area, center of gravity, etc.); make sure that
    # the blob list remaines sorted by area
    k = 0
    if iBlob > 0:
      while (k < iBlob) and (blobs[k].area > nFound): k += 1
      if k < iBlob:
        blobs.insert(k, blob_struct())
    blobs[k].ID   = iBlob
    blobs[k].area = nFound
    blobs[k].x    = by /nFound
    blobs[k].y    = bx /nFound
    blobs[k].prob = bp /nFound
    iBlob += 1
  nBlobs = iBlob

  # Copy blobs into list as function result
  tempL = []
  for i in range(nBlobs):
    if blobs[i].area > 0:
      tempL.append(blobs[i].as_list)

  # Return list of blobs, otherwise empty list
  return tempL

# ---------------------------------------------------------------------
