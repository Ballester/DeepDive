"""Deep dive libs"""
from input_data_levelDB_simulator_data_augmentation import DataSetManager
from config import *
from utils import *
from features_optimization import optimize_feature
from loss_network import *
from simulator import *

"""Structure"""
import sys
sys.path.append('structures')
sys.path.append('utils')
from inception_res_BAC_normalized import create_structure
from alex_discriminator import create_discriminator_structure

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
from scipy import misc
import glob

import json

"""Verifying options integrity"""
def verifyConfig(config):
  if config.restore not in (True, False):
    raise Exception('Wrong restore option. (True or False)')
  if config.save_features_to_disk not in (True, False):
    raise Exception('Wrong save_features_to_disk option. (True or False)')
  if config.save_json_summary not in (True, False):
    raise Exception('Wrong save_json_summary option. (True or False)') 
  if config.use_tensorboard not in (True, False):
    raise Exception('Wrong use_tensorboard option. (True or False)')
  if config.use_locking not in (True, False):
    raise Exception('Wrong use_locking option. (True or False)')
  if config.save_error_transmission not in (True, False):
    raise Exception('Wrong save_error_transmission option. (True or False)')
  if config.use_deconv not in (True, False):
    raise Exception('Wrong use_deconv option. (True or False)')
  if config.use_depths not in (True, False):
    raise Exception('Wrong use_depths option. (True or False)')



config = configMainSimulator()
verifyConfig(config)
""" Creating section"""
sess = tf.InteractiveSession()
c,binf,range_array=acquireProperties(config,sess)
dataset = DataSetManager(config) 
print dataset.getNImagesDataset()
global_step = tf.Variable(0, trainable=False, name="global_step")

"""creating plaholders"""
batch_size=config.batch_size
tf_images=tf.placeholder("float",(None,) +config.input_size, name="images")
tf_depths=tf.placeholder("float",(None,) +config.depth_size, name="depths")
tf_range=tf.placeholder("float",(None,)+range_array.shape[1:], name="ranges")
tf_c=tf.placeholder("float",(None,)+c.shape[1:], name="c")
tf_binf=tf.placeholder("float",(None,)+binf.shape[1:], name="binf")
lr = tf.placeholder("float", name = "learning_rate")

"""defining simulator structure"""
y_image = tf_images
x=applyTurbidity(y_image, tf_depths, tf_c, tf_binf, tf_range)

"""defining generative network structure"""
with tf.variable_scope("network", reuse=None):
  last_layer, dropoutDict, feature_maps,scalars,histograms = create_structure(tf, x,config.input_size,config.dropout)

network_vars=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='network')

"""define structure feature loss"""
feature_loss=create_loss_structure(tf, 255.0*last_layer, 255.0*tf_images, sess)

"""define discriminator structure for both ground truth and output"""
with tf.variable_scope('discriminator', reuse=None):
  d_score_gt=create_discriminator_structure(tf,y_image,config.input_size)
with tf.variable_scope('discriminator', reuse=True):
  d_score_output=create_discriminator_structure(tf,last_layer,config.input_size)

discriminator_vars=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='discriminator')

""" Creating losses for generative network"""
#lab_mse_loss = tf.reduce_mean(np.absolute(np.subtract(color.rgb2lab((255.0*last_layer).eval()), color.rgb2lab((255.0*y_image).eval()))))
mse_loss = tf.reduce_mean(tf.abs(tf.subtract(255.0*last_layer, 255.0*y_image)), reduction_indices=[1,2,3])



discriminator_loss=tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(labels=d_score_output, logits=tf.ones_like(d_score_output)))#tf.reduce_mean(-tf.log(tf.clip_by_value(tf.nn.sigmoid(d_score_output),1e-10,1.0)))#com log puro tava dando log(0)=NaN depois de um tempo
loss_function = (feature_loss+10*discriminator_loss)/2


""" Loss for descriminative network"""

#cross_entropy_real = tf.nn.sigmoid_cross_entropy_with_logits(d_score_gt, tf.ones_like(d_score_gt))
#disc_real_loss     = tf.reduce_mean(cross_entropy_real, name='disc_real_loss')
    
#cross_entropy_fake = tf.nn.sigmoid_cross_entropy_with_logits(d_score_output, tf.zeros_like(d_score_output))

#disc_fake_loss     = tf.reduce_mean(cross_entropy_fake, name='disc_fake_loss')

#discriminator_error = tf.add(disc_real_loss, disc_fake_loss)
#discriminator_error=tf.reduce_mean(-(tf.log(tf.clip_by_value(d_score_gt,1e-10,1.0))+tf.log(tf.clip_by_value(1-d_score_output,1e-10,1.0))))

train_step = tf.train.AdamOptimizer(learning_rate = lr, beta1=config.beta1, beta2=config.beta2, epsilon=config.epsilon,
                                    use_locking=config.use_locking).minimize(loss_function, var_list=network_vars)#treina so a rede, nao o discriminador

#disc_train_step = tf.train.AdamOptimizer(learning_rate = lr, beta1=config.beta1, beta2=config.beta2, epsilon=config.epsilon,
#                                    use_locking=config.use_locking).minimize(discriminator_error, var_list=discriminator_vars)#treina so o discriminador, sem mexer nos pesos da rede

"""Creating summaries"""

tf.summary.image('Input', x)
tf.summary.image('Output', last_layer)
tf.summary.image('GroundTruth', y_image)

ft_ops=[]
weights=[]
for key in config.features_list:
  ft_ops.append(feature_maps[key][0])
  weights.append(feature_maps[key][1])
for key in scalars:
  tf.summary.scalar(key,scalars[key])
for key in config.histograms_list:
  tf.histogram_summary('histograms_'+key, histograms[key])
tf.summary.scalar('Loss', tf.reduce_mean(loss_function))
tf.summary.scalar('feature_loss',tf.reduce_mean(feature_loss))
tf.summary.scalar('mse_loss',tf.reduce_mean(mse_loss))
tf.summary.scalar('learning_rate',lr)
# tf.summary.scalar('discriminator_score_groundtruth', tf.nn.sigmoid(tf.reduce_mean(d_score_gt)))
# tf.summary.scalar('discriminator_score_output', tf.nn.sigmoid(tf.reduce_mean(d_score_output)))
# tf.summary.scalar('discriminator_loss', discriminator_loss)
# tf.summary.scalar('discriminator_error', discriminator_error)

for ft, key in zip(ft_ops,config.features_list):
  for ch in xrange(ft.get_shape()[3]):
    summary_name=key+"_"+str(ch).zfill(len(str(ft.get_shape()[3])))
    tf.summary.scalar(summary_name, tf.reduce_mean(ft[:,:,:,ch]))

summary_op = tf.summary.merge_all()

val_error = tf.placeholder(tf.float32, shape=(), name="Validation_Error")
val_summary=tf.summary.scalar('Loss_Validation', val_error)

ft_summaries={}
deconv_summaries={}
ft_grid_placeholder=tf.placeholder(tf.float32, shape=(None, None, None, 1), name="Feature_Map_Activation")
d_grid_placeholder=tf.placeholder(tf.float32, shape=(None, None, None, 3), name="Deconvolution")
for key in config.features_list:
  ft_summaries[key]=tf.summary.image("features_map_"+key, ft_grid_placeholder)
  if config.use_deconv:
    deconv_summaries[key]=tf.summary.image("deconv_"+key, d_grid_placeholder)

weight_summaries={}
w_grid_placeholder=tf.placeholder(tf.float32, shape=(None, None, None, 3), name="Weights")
for key, w in zip(config.features_list, weights):
  if w is not None:
    weight_summaries[key]=tf.summary.image("weights_"+key, w_grid_placeholder)

opt_summaries={}
opt_grid_placeholder=tf.placeholder(tf.float32, shape=(None, None, None, 3), name="Optimization_Grid")
opt_placeholder=tf.placeholder(tf.float32, shape=(None, None, 3), name="Optimization")
for key, channel in config.features_opt_list:
  if channel<0:
    opt_summaries[key]=tf.summary.image("optimization_"+key, opt_grid_placeholder)
  else:
    n_channels=feature_maps[key][0].get_shape()[3]
    opt_name="optimization_"+key+"_"+str(channel).zfill(len(str(n_channels)))
    opt_summaries[opt_name]=tf.summary.image("optimization_"+opt_name, tf.expand_dims(opt_placeholder,0))

saver = tf.train.Saver(network_vars)

init_op=tf.global_variables_initializer()
sess.run(init_op)

summary_writer = tf.summary.FileWriter(config.summary_path, graph=sess.graph)

"""create dictionary to be saved in json""" #talves fazer em outra funcao
dados={} 
dados['learning_rate']=config.learning_rate
dados['beta1']=config.beta1
dados['beta2']=config.beta2
dados['epsilon']=config.epsilon
dados['use_locking']=config.use_locking
dados['summary_writing_period']=config.summary_writing_period
dados['validation_period']=config.validation_period
dados['batch_size']=config.batch_size
dados['variable_errors']=[]
dados['time']=[]
dados['variable_errors_val']=[]
dados['learning_rate_update']=[]

"""Load a previous model if restore is set to True"""

if not os.path.exists(config.models_path):
  os.mkdir(config.models_path)
ckpt = tf.train.get_checkpoint_state(config.models_path)

if config.restore and ckpt:
  print 'Restoring from ', ckpt.model_checkpoint_path
  saver.restore(sess,ckpt.model_checkpoint_path)
  tamanho=len(ckpt.model_checkpoint_path.split('-'))
  initialIteration = int(ckpt.model_checkpoint_path.split('-')[tamanho-1])
  
  if config.save_json_summary:
    if os.path.isfile(config.models_path +'summary.json'):
      outfile= open(config.models_path +'summary.json','r+')
      dados=json.load(outfile)
      outfile.close()
    else:
      outfile= open(config.models_path +'summary.json','w')
      json.dump(dados, outfile)
      outfile.close()
else:
  ckpt = 0
  initialIteration = 1

print 'Logging into ' + config.summary_path

"""Training"""
lowest_error = 1500;
lowest_val  = 1500;
lowest_iter = 1;
lowest_val_iter = 1;

"""training loop"""
training_start_time =time.time()
print config.n_epochs*dataset.getNImagesDataset()/config.batch_size
for i in range(initialIteration, config.n_epochs*dataset.getNImagesDataset()/config.batch_size):
  epoch_number = (float(i)*float(config.batch_size))/float(dataset.getNImagesDataset())
  """Save the model every model_saving_period iterations"""
  if i%config.model_saving_period == 0:
    saver.save(sess, config.models_path + 'model.ckpt', global_step=i)
    print 'Model saved.'


  start_time = time.time()

  batch = dataset.train.next_batch(config.batch_size)
  if config.use_depths:
    feedDict={tf_images: batch[0], tf_depths: batch[1], tf_range: range_array, tf_c: c, tf_binf: binf, lr: (config.learning_rate/(config.lr_update_value ** int(int(epoch_number)/config.lr_update_period)))}
  else:
    constant_depths=np.ones((batch_size,)+config.depth_size, dtype=np.float32);
    depths=constant_depths*10*np.random.rand(batch_size,1,1,1)
    feedDict={tf_images: batch[0], tf_depths: depths, tf_range: range_array, tf_c: c, tf_binf: binf, lr: (config.learning_rate/(config.lr_update_value ** int(int(epoch_number)/config.lr_update_period)))}
  sess.run(train_step, feed_dict=feedDict)#,disc_train_step], feed_dict=feedDict)

  duration = time.time() - start_time

  if i%8 == 0:
    examples_per_sec = config.batch_size / duration
    result=sess.run(loss_function, feed_dict=feedDict)#,discriminator_error], feed_dict=feedDict)
    result > 0
    train_accuracy = sum(result)/config.batch_size
    if  train_accuracy < lowest_error:
      lowest_error = train_accuracy
      lowest_iter = i
    print("Epoch %f step %d, images used %d, loss %g, lowest_error %g on %d,examples per second %f"
        %(epoch_number, i, i*config.batch_size, train_accuracy, lowest_error, lowest_iter,examples_per_sec))

  if i%config.summary_writing_period == 1 and (config.use_tensorboard or config.save_features_to_disk or config.save_json_summary):
    output, result, sim_input = sess.run([last_layer,loss_function, x], feed_dict=feedDict)
    result = np.mean(result)
    if len(ft_ops) > 0:
      ft_maps= sess.run(ft_ops, feed_dict=feedDict)
    else:
      ft_maps= []

    if config.use_deconv:
      deconv=deconvolution(x, feedDict, ft_ops, config.features_list, config.batch_size, config.input_size)
    else:
      deconv=[None]*len(ft_ops)

    if config.save_json_summary:
      dados['variable_errors'].append(float(result))
      dados['time'].append(time.time() - training_start_time)
      outfile = open(config.models_path +'summary.json','w')
      json.dump(dados, outfile)
      outfile.close()
    if config.use_tensorboard:
      summary_str = sess.run(summary_op, feed_dict=feedDict)
      summary_writer.add_summary(summary_str,i)
      if len(ft_ops) > 0:
        for ft, w, d, key in zip(ft_maps, weights, deconv, config.features_list):
          ft_grid=put_features_on_grid_np(ft)
          ft_summary=ft_summaries[key]
          summary_str=sess.run(ft_summary, feed_dict={ft_grid_placeholder:ft_grid})
          summary_writer.add_summary(summary_str,i)
          if w is not None:
            kernel=w.eval()
            kernel_grid=put_kernels_on_grid_np(kernel)
            kernel_summary=weight_summaries[key]
            kernel_summary_str=sess.run(kernel_summary, feed_dict={w_grid_placeholder:kernel_grid})
            summary_writer.add_summary(kernel_summary_str,i)
          if d is not None:
            deconv_grid=put_grads_on_grid_np(d.astype(np.float32))
            deconv_summary=deconv_summaries[key]
            deconv_summary_str=sess.run(deconv_summary, feed_dict={d_grid_placeholder:deconv_grid})
            summary_writer.add_summary(deconv_summary_str,i)
    if(config.save_features_to_disk):
      save_images_to_disk(output,sim_input,batch[0],config.summary_path)
      save_feature_maps_to_disk(ft_maps, weights, deconv, config.features_list,config.summary_path)

  if i%config.validation_period == 0:
    validation_result_error = 0
    for j in range(0,dataset.getNImagesValidation()/(config.batch_size)):
      #batch_val = dataset.validation.next_batch(config.batch_size)
      batch_val = dataset.validation.next_batch(config.batch_size)
      feedDictVal={tf_images: batch_val[0], tf_depths: batch_val[1], tf_range: range_array, tf_c: c, tf_binf: binf}
      #turbid_images=applyTurbidity(tf_images, tf_depths, tf_c, tf_binf, tf_range)
      #result=sess.run(turbid_images, feed_dict=feedDict)
      #feedDictVal = {x: result, y_: batch_val[0]}
      result = sess.run(loss_function, feed_dict=feedDictVal)
      validation_result_error += sum(result)
      if config.save_error_transmission:
        error_per_transmission=[0.0] * config.num_bins
        count_per_transmission=[0] * config.num_bins
        for i in range(len(batch_val[2])):
          index = int(float(batch_val[2][i]) * config.num_bins)
          error_per_transmission[index] += result[i]
          count_per_transmission[index] += 1
        for i in range(config.num_bins):
          if count_per_transmission[i]!=0:
            error_per_transmission[i] = error_per_transmission[i]/count_per_transmission[i]
        dados['error_per_transmission']=error_per_transmission

    if dataset.getNImagesValidation() !=0 :
      validation_result_error = (validation_result_error)/dataset.getNImagesValidation()
      
    if config.use_tensorboard:
      summary_str_val=sess.run(val_summary, feed_dict={val_error: validation_result_error})
      summary_writer.add_summary(summary_str_val,i)
    if config.save_json_summary:
      dados['variable_errors_val'].append(validation_result_error)
      outfile= open(config.models_path +'summary.json','w')
      json.dump(dados, outfile)
      outfile.close()

  if config.opt_every_iter>0 and i%config.opt_every_iter==0:
    """ Optimization """
    print("Running Optimization")
    for key, channel in config.features_opt_list:
        ft=feature_maps[key][0]
        n_channels=ft.get_shape()[3]
	opt_results=np.empty((1,)+config.input_size+(n_channels,), dtype=np.float32)
        if channel<0:
          #otimiza todos os canais
          for ch in xrange(n_channels):
            opt_output=optimize_feature(config.input_size, x, ft[:,:,:,ch])
            opt_results[0,:,:,:,ch]=opt_output
          # salvando as imagens como bmp
            if(config.save_features_to_disk):
              save_optimazed_image_to_disk(opt_output,ch,n_channels,key,config.summary_path)
          if config.use_tensorboard:
	    opt_grid=put_grads_on_grid_np(opt_results)
            opt_summary=opt_summaries[key]
            opt_summary_str=sess.run(opt_summary, feed_dict={opt_grid_placeholder:opt_grid})
            summary_writer.add_summary(opt_summary_str,i)

        else:
          opt_output=optimize_feature(config.input_size, x, ft[:,:,:,channel])
          if config.use_tensorboard:
            opt_name="optimization_"+key+"_"+str(channel).zfill(len(str(n_channels)))
            opt_summary=opt_summaries[opt_name]
            summary_str=sess.run(opt_summary, feed_dict={opt_placeholder:opt_output})
            summary_writer.add_summary(summary_str,i)
          # salvando as imagens como bmp
          if(config.save_features_to_disk):
            save_optimazed_image_to_disk(opt_output,channel,n_channels,key,config.summary_path)
