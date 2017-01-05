
def residual(tf, x,base_name,training=True):


  from deep_dive import DeepDive
  deep_dive = DeepDive()
  features={}
  scalars={}
  histograms={}

  x_image=x
  W_conv = deep_dive.weight_variable_scaling([3,3,64,64], name='W_conv1'+base_name)
  #conv = tf.nn.elu(tf.contrib.layers.batch_norm(deep_dive.conv2d(x_image, W_conv,strides=[1, 1, 1, 1], padding='SAME'),center=True,updates_collections=None,scale=True,is_training=training))
  conv = tf.nn.elu(deep_dive.conv2d(x_image, W_conv,strides=[1, 1, 1, 1], padding='SAME'))
  print conv
  features["conv"+base_name]=[conv,None]
  histograms["conv"+base_name]=W_conv

  W_conv2 = deep_dive.weight_variable_scaling([3,3,64,64], name='W_conv2'+base_name)
  #conv2 = tf.contrib.layers.batch_norm(deep_dive.conv2d(x_image, W_conv2,strides=[1, 1, 1, 1], padding='SAME'),center=True,updates_collections=None,scale=True,is_training=training)
  conv2 = deep_dive.conv2d(x_image, W_conv2,strides=[1, 1, 1, 1], padding='SAME')
  print conv2
  features["conv2"+base_name]=[conv2,None]
  histograms["conv2"+base_name]=W_conv2

  elu=tf.nn.elu(x_image+conv2)
  features["conv2"+base_name]=[elu,None]
  print elu
  
  return elu,features,histograms
