"""Deep dive libs"""
from input_data_dive_test import DataSetManager
from config import *

"""Structure"""
import sys
sys.path.append('structures')
sys.path.append('utils')
from depth_map_structure_dropout2 import create_structure

"""Core libs"""
import tensorflow as tf
import numpy as np

"""Visualization libs"""
import matplotlib.pyplot as plt
import matplotlib.cm as cm

"""Python libs"""
import os
from optparse import OptionParser
from PIL import Image
import subprocess
import time
from ssim_tf import ssim_tf
from features_on_grid import *
from features_optimization import optimize_feature

"""Verifying options integrity"""
config= configMain()

if config.restore not in (True, False):
  raise Exception('Wrong restore option. (True or False)')

dataset = DataSetManager(config.training_path, config.validation_path, config.training_path_ground_truth,config.validation_path_ground_truth, config.input_size, config.output_size)
global_step = tf.Variable(0, trainable=False, name="global_step")


""" Creating section"""
x = tf.placeholder("float", name="input_image")
y_ = tf.placeholder("float", name="output_image")
sess = tf.InteractiveSession()
last_layer, dropoutDict, feature_maps,weights,scalars,histograms = create_structure(tf, x,config.input_size,config.dropout)

" Creating comparation metrics"
y_image = y_
loss_function = tf.sqrt(tf.reduce_mean(tf.pow(tf.sub(last_layer, y_image),2)))
# using the same function with a different name
loss_validation = tf.sqrt(tf.reduce_mean(tf.pow(tf.sub(last_layer, y_image),2)),name='Validation')
#loss_function_ssim = ssim_tf(tf,y_image,last_layer)

train_step = tf.train.AdamOptimizer(config.learning_rate).minimize(loss_function)

"""Creating summaries"""

tf.image_summary('Input', x)
tf.image_summary('Output', last_layer)
tf.image_summary('GroundTruth', y_)
#tf.image_summary('Output', tf.reshape(tf.image.grayscale_to_rgb(last_layer),[16,16,3,1]))
#tf.image_summary('GroundTruth', tf.reshape(tf.image.grayscale_to_rgb(y_),[16,16,3,1]))

#for key in config.features_list:
# tf.image_summary('Features_map_'+key, put_features_on_grid_tf(feature_maps[key], 4))
ft_ops=[]
for key in config.features_list:
  ft_ops.append(feature_maps[key])
for key in scalars:
  tf.scalar_summary(key,scalars[key])
for key in config.histograms_list:
  tf.histogram_summary('histograms_'+key, histograms[key])
tf.scalar_summary('Loss', loss_function)
#tf.scalar_summary('Loss_SSIM', loss_function_ssim)

summary_op = tf.merge_all_summaries()
saver = tf.train.Saver(tf.all_variables())

val  =tf.scalar_summary('Loss_Validation', loss_validation)

sess.run(tf.initialize_all_variables())

summary_writer = tf.train.SummaryWriter(config.summary_path,
                                            graph=sess.graph)

"""Load a previous model if restore is set to True"""

if not os.path.exists(config.models_path):
  os.mkdir(config.models_path)
ckpt = tf.train.get_checkpoint_state(config.models_path)
if config.restore:
  if ckpt:
    print 'Restoring from ', ckpt.model_checkpoint_path  
    saver.restore(sess,ckpt.model_checkpoint_path)
else:
  ckpt = 0

print 'Logging into ' + config.summary_path

"""Training"""

lowest_error = 1.5;
lowest_val  = 1.5;
lowest_iter = 1;
lowest_val_iter = 1;

feedDict=dropoutDict
if ckpt:
  initialIteration = int(ckpt.model_checkpoint_path.split('-')[1])
else:
  initialIteration = 1

for i in range(initialIteration, config.n_epochs*dataset.getNImagesDataset()):

  
  epoch_number = 1.0+ (float(i)*float(config.batch_size))/float(dataset.getNImagesDataset())


  
  """ Do validation error and generate Images """
  batch = dataset.train.next_batch(config.batch_size)
  
  """Save the model every 300 iterations"""
  if i%300 == 0:
    saver.save(sess, config.models_path + 'model.ckpt', global_step=i)
    print 'Model saved.'

  start_time = time.time()
  #print batch[0].shape
  feedDict.update({x: batch[0], y_: batch[1]})
  sess.run(train_step, feed_dict=feedDict)
  
  duration = time.time() - start_time

  if i%20 == 0:
    num_examples_per_step = config.batch_size 
    examples_per_sec = num_examples_per_step / duration
    train_accuracy = sess.run(loss_function, feed_dict=feedDict)
    if  train_accuracy < lowest_error:
      lowest_error = train_accuracy
      lowest_iter = i
    print("Epoch %f step %d, images used %d, loss %g, lowest_error %g on %d,examples per second %f"%(epoch_number, i, i*config.batch_size, train_accuracy, lowest_error, lowest_iter,examples_per_sec))

  """ Writing summary, not at every iterations """
  if (i%20 == 0 and (config.use_tensorboard or config.save_features_to_disk)):

    batch_val = dataset.validation.next_batch(config.batch_size)    
    result= sess.run(last_layer, feed_dict=feedDict)      
    ft_maps=sess.run(ft_ops,feed_dict=feedDict)

#   start = time.time()
    if config.use_tensorboard:
     summary_str_val= sess.run(val, feed_dict=feedDict)
     summary_str = sess.run(summary_op, feed_dict=feedDict)
     summary_writer.add_summary(summary_str,i)
     
     for ft, key in zip(ft_maps,config.features_list):
      ft_grid=put_features_on_grid_np(ft)
      ft_name="Features_map_"+key
      ft_summary=tf.image_summary(ft_name, ft_grid)
      summary_str=sess.run(ft_summary)
      summary_writer.add_summary(summary_str,i)
      wkey="W_"+key
      if wkey in weights:
       kernel=weights[wkey].eval()
       kernel_grid=put_kernels_on_grid_np(kernel)
       kernel_name="kernels_"+key
       kernel_summary=tf.image_summary(kernel_name, kernel_grid)
       kernel_summary_str=sess.run(kernel_summary)
       summary_writer.add_summary(kernel_summary_str,i)
#   end = time.time()
#   print "summary time:"
#   print(end - start)

#   start = time.time()
    if(config.save_features_to_disk):
     result_imgs=(result * 255).round().astype(np.uint8)
     for j in xrange(result_imgs.shape[0]):
      im = Image.fromarray(result_imgs[j])
      file_name="output.bmp"
      im_folder=str(j).zfill(len(str(result_imgs.shape[0])))
      folder_name=config.summary_path+"/output/"+im_folder
      if not os.path.exists(folder_name):
       os.makedirs(folder_name)
      im.save(folder_name+"/"+file_name)

     input_imgs=(batch[0] * 255).round().astype(np.uint8)
     for j in xrange(input_imgs.shape[0]):
      im = Image.fromarray(input_imgs[j])
      file_name="input.bmp"
      im_folder=str(j).zfill(len(str(input_imgs.shape[0])))
      folder_name=config.summary_path+"/input/"+im_folder
      if not os.path.exists(folder_name):
       os.makedirs(folder_name)
      im.save(folder_name+"/"+file_name)
    
     gt_imgs=(batch[1] * 255).round().astype(np.uint8)
     for j in xrange(gt_imgs.shape[0]):
      im = Image.fromarray(gt_imgs[j])
      file_name="ground_truth.bmp"
      im_folder=str(j).zfill(len(str(gt_imgs.shape[0])))
      folder_name=config.summary_path+"/ground_truth/"+im_folder
      if not os.path.exists(folder_name):
       os.makedirs(folder_name)
      im.save(folder_name+"/"+file_name) 

      for ft, key in zip(ft_maps,config.features_list):
       ft_img = (ft - ft.min())
       ft_img*=(255/ft_img.max())
       for k in xrange(ft.shape[0]):
        for l in xrange(ft.shape[3]):
         ch_img=ft_img[k,:,:,l].astype(np.uint8) 
         im = Image.fromarray(ch_img)
         file_name=str(l).zfill(len(str(ft.shape[3])))+".bmp"
         im_folder=str(k).zfill(len(str(ft.shape[0])))
         folder_name=config.summary_path+"/feature_maps/"+key+"/"+im_folder
         if not os.path.exists(folder_name):
          os.makedirs(folder_name)
         im.save(folder_name+"/"+file_name)
       wkey="W_"+key
       if wkey in weights:
        kernel=weights[wkey].eval()
	kernel_img = (kernel - kernel.min())
        kernel_img*=(255/kernel_img.max())
	for k in xrange(kernel_img.shape[3]):
         im = Image.fromarray(kernel_img[:,:,:,k].astype(np.uint8))
	 k_file_name="W_"+str(k).zfill(len(str(ft.shape[3])))+".bmp"
         k_folder_name=config.summary_path+"/feature_maps/"+key+"/kernels"
	 if not os.path.exists(k_folder_name):
          os.makedirs(k_folder_name)
	 im.save(k_folder_name+"/"+k_file_name)
	
#   end = time.time()
#   print "saving time:"
#   print(end - start)

    """ Check here the weights """
    #result = Image.fromarray((result[0,:,:,:]*255).astype(np.uint8))
    #result.save(config.validation_path_ground_truth + str(str(i)+ '.jpg'))
    #summary_writer.add_summary(summary_str_val,i)
  if config.opt_every_iter>0 and i%config.opt_every_iter==0:
    """ Optimization """
    print("Running Optimization")
    for key, channel in config.features_opt_list:
     ft=feature_maps[key]
     n_channels=ft.get_shape()[3]
     if channel<0:
      #otimiza todos os canais       
      for ch in xrange(n_channels):
	opt_output=optimize_feature(config.input_size, x, ft[:,:,:,ch])
	if config.use_tensorboard:
	 opt_name="optimization_"+key+"_"+str(ch).zfill(len(str(n_channels)))
	 opt_summary=tf.image_summary(opt_name, np.expand_dims(opt_output,0))
	 summary_str=sess.run(opt_summary)
	 summary_writer.add_summary(summary_str,i)
# salvando as imagens como bmp
	if(config.save_features_to_disk):
         opt_output_rescaled = (opt_output - opt_output.min())
         opt_output_rescaled*=(255/opt_output_rescaled.max())
         im = Image.fromarray(opt_output_rescaled.astype(np.uint8))
         file_name="opt_"+str(ch).zfill(len(str(n_channels)))+".bmp"
         folder_name=config.summary_path+"/feature_maps/"+key+"/optimization"
         if not os.path.exists(folder_name):
          os.makedirs(folder_name)
         im.save(folder_name+"/"+file_name)	
     else:
      opt_output=optimize_feature(config.input_size, x, ft[:,:,:,channel])
      if config.use_tensorboard:
       opt_name="optimization_"+key+"_"+str(channel).zfill(len(str(n_channels)))
       opt_summary=tf.image_summary(opt_name, np.expand_dims(opt_output,0))
       summary_str=sess.run(opt_summary)
       summary_writer.add_summary(summary_str,i)
# salvando as imagens como bmp
      if(config.save_features_to_disk):
       opt_output_rescaled = (opt_output - opt_output.min())
       opt_output_rescaled*=(255/opt_output_rescaled.max())
       im = Image.fromarray(opt_output_rescaled.astype(np.uint8))
       file_name="opt_"+str(channel).zfill(len(str(n_channels)))+".bmp"
       folder_name=config.summary_path+"/feature_maps/"+key+"/optimization"
       if not os.path.exists(folder_name):
        os.makedirs(folder_name)
       im.save(folder_name+"/"+file_name)

