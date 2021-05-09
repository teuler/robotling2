#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# blob.py
# Function for blob detection in images
#
# The MIT License (MIT)
# Copyright (c) 2019 Thomas Euler
# 2020-08-21, v1.0 Analogous to the `blob.c` code, pure MicroPython
#
# ---------------------------------------------------------------------
import array
import math
from micropython import const
from robotling_lib.misc.helpers import timed_function

# pylint: disable=bad-whitespace
MAX_BLOBS          = const(5)
MAX_BLOB_FIELDS    = const(5)
xoffs              = [-1, 1,  0, 0]
yoffs              = [ 0, 0, -1, 1]
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
  """ Dummy
  """
  return img

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
  pImg = array.array("f", [0]*n)
  for i in range(n):
    pImg[i] = img[i]

  # Calculate mean and sd across (filtered) image to determine threshold
  avg = sum(pImg) /n
  _sum = 0
  for i in range(n):
    _sum += math.pow(pImg[i] -avg, 2)
  sd = math.sqrt(_sum /(n-1))
  thres = avg +sd *nsd

  # Find blob(s) ...
  #
  # Mark all pixels above the threshold
  pMsk = array.array("B", [0]*n)
  pPrb = array.array("f", [0]*n)
  nThres = 0
  for i in range(n):
    if pImg[i] >= thres:
      pMsk[i] = 255
      pPrb[i] = (pImg[i] -avg) /sd
      nThres += 1

  # Check if these above-threshold pixels represent continuous blobs
  nLeft = nThres
  iBlob = 0
  while nLeft > 0 and iBlob < MAX_BLOBS:
    # As long as unassigned mask pixels are left, continue going over the image
    for y in range(dy):
      for x in range(dx):
        if pMsk[x +y*dx] == 255:
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

          # Store blob properties (area, center of gravity, etc.); make sure
          # that the blob list remaines sorted by area
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
