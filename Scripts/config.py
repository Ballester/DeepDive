
"""configuration file"""

class configMain:
	def __init__(self):
		self.learning_rate = 1e-7
		self.beta1=0.9
		self.beta2=0.999
		self.epsilon=1e-08
		self.use_locking=False
		self.batch_size = 32
		self.batch_size_val = 64
		self.variable_names = ['MSE']
		self.n_epochs = 80   # the number of epochs that we are going to run
		self.leveldb_path = '../../DeepDive-master/datasets/datasetDepthV3/'
		self.training_path = '../../DeepDive-master/datasets/datasetDepthV3/Training/'
		self.training_path_ground_truth = '../../DeepDive-master/datasets/datasetDepthV3/GroundTruth'
		self.validation_path = '../../DeepDive-master/datasets/datasetDepthV3/Validation/'
		self.summary_path = '/tmp/new_26_7/'
		self.validation_path_ground_truth = '../../DeepDive-master/datasets/datasetDepthV3/ValidationGroundTruth/'
		self.models_path = 'models/new_26_7/'
		self.input_size = (224, 224, 3)
		self.output_size = (224, 224, 3)
		self.ground_truth_size = (224,224, 3)
		self.restore = False
		self.dropout = [1,1,1,1]
		self.summary_writing_period = 4
		self.validation_period = 16
		self.histograms_list=[]
		self.features_list=[]#"S1_conv1","S1_pool1","S1_pool2","S3_incep1"]
		self.features_opt_list=[]#["S1_conv1", 0],["S1_conv1", 63],["S3_incep1",0]]
		self.opt_every_iter=0
		self.save_features_to_disk=False
		self.use_tensorboard=False

class configDehazeNet:
	def __init__(self):
		self.learning_rate = 5*1e-6
		self.init_std_dev=0.01
		self.batch_size = 5
		self.n_epochs = 80   # the number of epochs that we are going to run
		self.training_path = '../datasets/dataset4_2/Training'
		self.training_path_ground_truth = '../datasets/dataset4_2/Transmission'
		self.validation_path = '../datasets/dataset4_2/Validation'
		self.summary_path = '/tmp/dataset43q'
		self.validation_path_ground_truth = '../datasets/dataset4_2/ValidationTransmission/'
		self.models_path = 'models/'
		self.input_size = (16, 16, 3)
		self.output_size = (1, 1)
		self.ground_truth_size = (16,16)
		self.restore = False
		self.dropout = []
		self.features_list=[["conv1",2],["conv2_1",1],["incep1_3_3",4],["incep1_5_5",4],["incep1_7_7",4]]
		self.histograms_list=["W_conv1","b_conv1","W_incep1_3_3","W_incep1_5_5","W_incep1_7_7"]
		self.evaluate_path = '/home/nautec/DeepDive/Local_results/'
		self.evaluate_out_path ='/home/nautec/DeepDive/Local_results/RealImageTransmission/'
		self.opt_every_iter=100

class configDehazeNOT:
	def __init__(self):
		self.learning_rate = 5*1e-6
		self.init_std_dev=0.01
		self.batch_size = 5
		self.n_epochs = 80   # the number of epochs that we are going to run
		self.training_path = '../datasets/dataset4_2/Training'
		self.training_path_ground_truth = '../datasets/dataset4_2/Transmission'
		self.validation_path = '../datasets/dataset4_2/Validation'
		self.summary_path = '/tmp/dataset43t'
		self.validation_path_ground_truth = '../datasets/dataset4_2/ValidationTransmission/'
		self.models_path = 'models/'
		self.input_size = (16, 16, 3)
		self.output_size = (16, 16, 1)
		self.ground_truth_size = (16,16)
		self.restore = False
		self.dropout = []
		self.features_list=[["conv1",2],["conv2",4],["conv3",4],["pool1",2],["conv4",8]]
		self.histograms_list=["W_conv1","b_conv1","W_conv2","b_conv2","W_conv3", "b_conv3", "W_conv4", "b_conv4"]
		self.evaluate_path = '/home/nautec/DeepDive/Local_results/RealImages/'
		self.evaluate_out_path ='/home/nautec/DeepDive/Local_results/RealImageTransmission/'
		self.opt_every_iter=100

class configPathfinder:
	def __init__(self):
		self.learning_rate = 5*1e-7
		self.init_std_dev=0.01
		self.batch_size = 5
		self.batch_size_val = 2048
		self.n_epochs = 80   # the number of epochs that we are going to run
		self.training_path = '../datasets/UDataset16x16/Training'
		self.training_path_ground_truth = '../datasets/UDataset16x16/Transmission'
		self.validation_path = '../datasets/UDataset16x16/Validation'
		self.summary_path = '/tmp/transmission_25_7'
		self.validation_path_ground_truth = '../datasets/UDataset16x16/ValidationTransmission/'
		self.models_path = 'models/transmission_25_7/'
		self.input_size = (16, 16, 3)
		self.output_size = (1, 1)
		self.ground_truth_size = (16, 16)
		self.restore = False
		self.dropout = []
		self.features_list=[["conv1",4],["conv2",4],["conv3",8],["conv4",8],["pool1",8],["conv5",1]]
		self.histograms_list=["W_conv1","b_conv1","W_conv2","b_conv2","W_conv3", "b_conv3", "W_conv4", "b_conv4", "W_conv5", "b_conv5"]
		self.evaluate_path = '/home/nautec/DeepDive/Local_results/'
		self.evaluate_out_path ='/home/nautec/DeepDive/Local_results/RealImageTransmission/'
		self.opt_every_iter=100

class configOptimization:
	def __init__(self):
		self.opt_step=1
		self.opt_n_iters=50
		self.decay=0
		self.blur_iter=0
		self.blur_width=1
		self.norm_pct_thrshld=0
		self.contrib_pct_thrshld=0
		self.lap_grad_normalization=True
