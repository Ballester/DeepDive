"""Deep dive libs"""
from input_data_dive_test import DataSetManager
from config import *

"""Structure"""
import sys
sys.path.append('structures')
sys.path.append('utils')
from inception_res_BAC import create_structure

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
from features_on_grid import put_features_on_grid_np
from scipy import misc

"""Verifying options integrity"""
config= configMain()

def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
    #fig.show()
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    image = np.fromstring ( fig.canvas.tostring_rgb(), dtype=np.uint8 )
    image.shape = (1, w, h,3 )



    #image = np.asarray(image)
    #image = image.astype(np.float32)
    #image = np.multiply(image, 1.0 / 255.0)


 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    #buf = np.roll ( buf, 3, axis = 2 )
  
    #image = np.empty((1,w,h,3))
    #image[0] = buf
    return image




if config.restore not in (True, False):
  raise Exception('Wrong restore option. (True or False)')

dataset = DataSetManager(config.training_path, config.validation_path, config.training_path_ground_truth,config.validation_path_ground_truth, config.input_size, config.output_size)
global_step = tf.Variable(0, trainable=False, name="global_step")


""" Creating section"""
x = tf.placeholder("float", name="input_image")
y_ = tf.placeholder("float", name="output_image")
plot_image = tf.placeholder("float", name="output_image_1")
sess = tf.InteractiveSession()
last_layer, dropoutDict, feature_maps,scalars,histograms = create_structure(tf, x,config.input_size,config.dropout)



" Creating comparation metrics"
y_image = y_
loss_function = tf.sqrt(tf.reduce_mean(tf.pow(tf.sub(last_layer, y_image),2)))
# using the same function with a different name
#loss_validation = tf.sqrt(tf.reduce_mean(tf.pow(tf.sub(last_layer, y_image),2)),name='Validation')
#loss_function_ssim = ssim_tf(tf,y_image,last_layer)

train_step = tf.train.AdamOptimizer(config.learning_rate).minimize(loss_function)

"""Creating summaries"""

tf.image_summary('Input', x)
tf.image_summary('Output', last_layer)#tf.reshape(tf.image.grayscale_to_rgb(last_layer),[16,16,3,1]))
tf.image_summary('GroundTruth',y_image) #tf.reshape(tf.image.grayscale_to_rgb(y_),[16,16,3,1]))

#test = tf.get_default_graph().get_tensor_by_name("scale_1/Scale1_first_relu:0")
#tf.image_summary('Teste', put_features_on_grid(test, 8))
#for key, l in config.features_list:
# tf.image_summary('Features_map_'+key, put_features_on_grid(feature_maps[key], l))
#for key in scalars:
#  tf.scalar_summary(key,scalars[key])
#for key in config.histograms_list:
#  tf.histogram_summary('histograms_'+key, histograms[key])
#tf.image_summary('Plot Image',plot_image)
#tf.scalar_summary('Loss', loss_function)
#tf.scalar_summary('Loss_SSIM', loss_function_ssim)

summary_op = tf.merge_all_summaries()
saver = tf.train.Saver(tf.all_variables())

#val  =tf.scalar_summary('Loss_Validation', loss_validation)

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



print config.n_epochs*dataset.getNImagesDataset() 


error_vec = []
val_error_vec = []
iteration = []
iteration_val = []

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

  if i%2 == 0:
    num_examples_per_step = config.batch_size 
    examples_per_sec = num_examples_per_step / duration
    train_accuracy = sess.run(loss_function, feed_dict=feedDict)
    if  train_accuracy < lowest_error:
      lowest_error = train_accuracy
      lowest_iter = i
    print("Epoch %f step %d, images used %d, loss %g, lowest_error %g on %d,examples per second %f"%(epoch_number, i, i*config.batch_size, train_accuracy, lowest_error, lowest_iter,examples_per_sec))

  """ Writing summary, not at every iterations """
  if i%20 == 1:
    
    
    result= sess.run(loss_function, feed_dict=feedDict)
    
    iteration.append(i)
    error_vec.append(result)
    

    #print iteration
    #print error_vec
    #print val_error_vec

   
    #plot_image = fig2data(figure)
    #print fig2data(figure).dtype

    #addedimage = sess.run(z,feed_dict={plot_image:fig2data(figure)})

    summary_str = sess.run(summary_op, feed_dict=feedDict)
    #summary_str_val,result 

    summary_writer.add_summary(summary_str,i)

    

    """ Check here the weights """
    #result = Image.fromarray((result[0,:,:,:]*255).astype(np.uint8))
    #result.save(config.validation_path_ground_truth + str(str(i)+ '.jpg'))
    #summary_writer.add_summary(summary_str_val,i)


    print config.features_list
    for key in config.features_list:
      print key
      print feature_maps
      comp_feature_map = sess.run(feature_maps[key], feed_dict= feedDict)
      grid_output = put_features_on_grid_np(comp_feature_map)

      print grid_output.shape
      if not os.path.exists(config.models_path + '/' + key):
        os.makedirs(config.models_path + '/' + key)

      misc.imsave(config.models_path + '/' + key  + '/' + str(i) + '.png', grid_output)




  if i%2 == 1:

    print ' VALIDATING '
    iteration_val.append(i)
    summary_str_val = 0
    for j in range(1,dataset.getNImagesValidation()/(8*config.batch_size_val)):
      batch_val = dataset.validation.next_batch(config.batch_size_val)

      #print feature_maps

      summary_str_val +=  sess.run(loss_function, feed_dict={x: batch_val[0], y_: batch_val[1]})
      print j

    val_error_vec.append(summary_str_val/len(range(1,dataset.getNImagesValidation()/(8*config.batch_size_val))))
    figure = plt.figure(  )
    plot   = figure.add_subplot ( 111 )
    plot.plot(iteration, error_vec, 'b-', iteration_val, val_error_vec, 'r-')
    figure.savefig(config.models_path + str(i) + '.png')




      


