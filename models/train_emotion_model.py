import numpy as np
import pandas as pd
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Dropout, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical

# FER2013 dataset file
DATASET_PATH = "data/fer2013.csv"

# emotion labels
emotion_labels = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral"
]

print("Loading dataset...")

data = pd.read_csv(DATASET_PATH)

pixels = data["pixels"].tolist()

faces = []

for pixel_sequence in pixels:
    
    face = np.array(pixel_sequence.split(" "), dtype="float32")
    
    face = face.reshape(48, 48)
    
    faces.append(face)

faces = np.array(faces)

faces = np.expand_dims(faces, -1)

faces = faces / 255.0

emotions = pd.get_dummies(data["emotion"]).values

print("Dataset loaded")

# CNN model
model = Sequential()

model.add(Conv2D(32, (3,3), activation="relu", input_shape=(48,48,1)))
model.add(MaxPooling2D(2,2))

model.add(Conv2D(64, (3,3), activation="relu"))
model.add(MaxPooling2D(2,2))

model.add(Conv2D(128, (3,3), activation="relu"))
model.add(MaxPooling2D(2,2))

model.add(Flatten())

model.add(Dense(128, activation="relu"))
model.add(Dropout(0.5))

model.add(Dense(7, activation="softmax"))

model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

print("Training model...")

model.fit(
    faces,
    emotions,
    batch_size=64,
    epochs=30,
    validation_split=0.2
)

print("Saving model...")

model.save("models/emotion_model.hdf5")

print("Model saved successfully")