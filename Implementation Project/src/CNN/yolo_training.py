# 
# THE TRAINING FOR YOLOv26
# 
# DO NOT RUN UNLESS YOU ARE EXPLICITLY TRAINING THE MODEL
# 

from ultralytics import YOLO
from roboflow import Roboflow

# Download dataset from Roboflow
rf = Roboflow(api_key="rnkQazKZ1p4ibFE0Kq4Z")
project = rf.workspace("project-house-gsz5t").project("cs440-drone-cnn-model")
version = project.version(1)
dataset = version.download("yolo26")

# Load a model
model = YOLO("yolo26n.pt")

# Train the model on the new Roboflow dataset
results = model.train(data=f"{dataset.location}/data.yaml", epochs=10, imgsz=640, workers=4)
