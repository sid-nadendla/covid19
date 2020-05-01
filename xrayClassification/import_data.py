import cv2
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import random

import tensorflow
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras import optimizers
from tensorflow.keras import backend as K
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, BatchNormalization

# For Grad-CAM
from tensorflow.keras import activations
from vis.visualization import visualize_cam, overlay
from vis.utils import utils
import matplotlib.cm as cm

class CovidChestXrays:
    DATADIR = "D:/Research/COVID/myCNN - Copy/images"
    CATEGORIES = ["covid-19", "no covid-19"]

    training_set = []
    nrows, ncolumn = 150, 150

    def training_data(self):
        for category in self.CATEGORIES:
            path = os.path.join(self.DATADIR, category)
            label_num = self.CATEGORIES.index(category)
            for img in os.listdir(path):
                try:
                    arr = cv2.resize(cv2.imread(os.path.join(path,img), cv2.IMREAD_GRAYSCALE), (self.nrows, self.ncolumn), interpolation=cv2.INTER_CUBIC)
                    self.training_set.append([arr, label_num])
                except Exception as _:
                    pass

        random.shuffle(self.training_set)

    def preprocess_images(self):
        X, y = [], []
        for img, label in self.training_set:
            X.append(img)
            y.append(label)

        X = np.array(X).reshape(-1, self.nrows, self.ncolumn, 1)
        y = np.array(y)

        X = X / 255

        return X, y

    def cnn_model(self, X, y):
        model = Sequential()
        model.add(Conv2D(64, (3,3), input_shape=X.shape[1:]))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2,2)))

        model.add(Conv2D(64, (3,3)))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2,2)))

        model.add(Flatten())
        model.add(Dense(64))

        model.add(Dense(1))
        model.add(Activation('sigmoid'))

        model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])

        model.fit(X, y, batch_size=5, epochs=3, validation_split=0.1)

        model.add(Dense(2, activation='softmax', name='visualized_layer'))

        print('Model',model)
        model.save('covid-classifier.h5')
        # self.apply_gradcam(model)

c19 = CovidChestXrays()
c19.training_data()
print("Training complete")

X, y = c19.preprocess_images()
print("Preprocess complete")

c19.cnn_model(X, y)
print("Model Trained")
# c19.apply_gradcam('model')