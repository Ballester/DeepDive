from __future__ import absolute_import
from __future__ import division
import gzip
import os
import numpy as np
import Image, colorsys
from scipy import misc
from six.moves import urllib
from six.moves import xrange  # pylint: disable=redefined-builtin
import random
import glob
import leveldb
import matplotlib.pyplot as plt
from time import time
from config import *

def readImageFromDB(db, key, size):
  image =  np.reshape(np.fromstring(db.Get(key),dtype=np.float32),size)
  return image

class DataSet(object):
  def __init__(self, images_key, input_size,depth_size, num_examples,db,validation,invert,rotate):
    self._db=db
    self._is_validation = validation
    self._num_examples = num_examples
    self._images_key = images_key
    random.shuffle(self._images_key)
    self._epochs_completed = 0
    self._index_in_epoch = 0
    self._input_size= input_size
    self._depth_size= depth_size
    self.invert = invert
    self.rotate = rotate

  def getTransmission(n):
    self._db.Get(str(n))

  def next_batch(self, batch_size):
    """Return the next `batch_size` examples from this data set."""
    start = self._index_in_epoch
    self._index_in_epoch += batch_size
    if batch_size >  (self._num_examples - self._index_in_epoch):
      # Finished epoch
      print 'end epoch'
      self._epochs_completed += 1
      # Shuffle the data
      """ Shufling all the Images with a single permutation """
      random.shuffle(self._images_key)
      start = 0
      self._index_in_epoch = batch_size
      assert batch_size <= self._num_examples

    images = np.empty((batch_size, self._input_size[0], self._input_size[1],self._input_size[2]))
    if len(self._depth_size)==2:
      self._depth_size = (self._depth_size[0], self._depth_size[1],1)
    depths = np.empty((batch_size, self._depth_size[0], self._depth_size[1],self._depth_size[2]))
    for n in range(batch_size):
      key=self._images_key[start+n]
      rotation=0
      inversion=0
      if self.rotate:
        rotation=key & 3
        key=int(key/4)

      if self.invert:
        inversion=key & 1
        key=int(key/2)
        
      if self._is_validation:
        images[n] = readImageFromDB(self._db,'val'+str(key),self._input_size)
        depths[n] = readImageFromDB(self._db,'val'+str(key)+"depth",self._depth_size)
      else:
        images[n] = readImageFromDB(self._db,str(key),self._input_size)
        depths[n] = readImageFromDB(self._db,str(key)+"depth",self._depth_size)

      images[n]=np.rot90(images[n],rotation)
      depths[n]=np.rot90(depths[n],rotation)

      if inversion:
        images[n]=np.fliplr(images[n])
        depths[n]=np.fliplr(depths[n])
    return images, depths#, transmission


class DataSetManager(object):
  def __init__(self, config):
    self.input_size = config.input_size
    self.depth_size = config.depth_size
    self.db = leveldb.LevelDB(config.leveldb_path + 'db') 
    self.num_examples = int(self.db.Get('num_examples'))
    self.num_examples_val = int(self.db.Get('num_examples_val'))
    if config.invert:
      self.num_examples = self.num_examples * 2
      self.num_examples_val= self.num_examples_val * 2
    if config.rotate:
      self.num_examples = self.num_examples * 4
      self.num_examples_val= self.num_examples_val * 4
    self.images_key = range(self.num_examples)
    self.images_key_val = range(self.num_examples_val)
    # for i in range(self.num_examples_val):
    #   self.images_key_val[i] = 'val' + str(i)
    self.train = DataSet(self.images_key,config.input_size,config.depth_size,self.num_examples,self.db,validation=False,invert=config.invert,rotate=config.rotate)
    self.validation = DataSet(self.images_key_val,config.input_size,config.depth_size,self.num_examples_val,self.db,validation=True,invert=config.invert,rotate=config.rotate)

  def getNImagesDataset(self):
    return self.num_examples

  def getNImagesValidation(self):
    return self.num_examples_val
