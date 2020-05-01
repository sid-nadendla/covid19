########################################################################
# This class is used to predict COVID-19 using patients x-ray image
# Author: Mukund Telukunta(mt3qb@mst.edu)
# ######################################################################
import os
import cv2
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import tensorflow as tf
import keras
from keras import activations
from keras.models import load_model

from vis.visualization import visualize_cam, overlay
from vis.utils import utils
import matplotlib.cm as cm

from google.cloud import storage

class xrayClassification:
	def __init__(self):
		pass

	def classifier(self,img):
		testResult = 'Cannot Determine'
		print("***********",type(img))
		#Loading trained model from file
		model = load_model(os.getcwd()+"/xrayClassification/"+'xray-classifier.h5')
		# accessing image from google cloud storage

		try:
			input_image = cv2.resize(cv2.imdecode(img, cv2.IMREAD_GRAYSCALE), (150, 150), interpolation=cv2.INTER_CUBIC)
		except Exception as _:
			pass

		input_image = np.array(input_image).reshape(-1, 150, 150, 1)
		input_image = input_image / 255
		print('Input shape', input_image.shape)

		preds = model.predict(input_image)
		input_class = np.argmax(preds[0])

		layer_index = utils.find_layer_idx(model, 'visualized_layer')

		model.layers[layer_index].activation = activations.linear
		model = utils.apply_modifications(model) 

		print('Done so far.')

		fig, axes = plt.subplots(1, 3)

		visualization = visualize_cam(model, layer_index, filter_indices=input_class, seed_input=input_image)
		axes[0].imshow(input_image.squeeze(), cmap='gray') 
		axes[0].set_title('Input')
		axes[1].imshow(visualization)
		axes[1].set_title('Grad-CAM')
		# heatmap = np.uint8(cm.jet(visualization)[..., :3] * 255)
		jet_heatmap = np.uint8(cm.jet(visualization) * 255)[:, : , :, 0]
		original = np.uint8(cm.gray(input_image.squeeze())[..., :3] * 255)
		# axes[2].imshow(overlay(heatmap, original))
		axes[2].imshow(overlay(jet_heatmap, original))
		axes[2].set_title('Overlay')
		fig.suptitle(f'Image Class = {input_class}')
		fig_to_upload = plt.gcf()

		if input_class == 0:
			testResult = 'Positive'
		else:
			testResult = 'Negative'
		return fig_to_upload,testResult
