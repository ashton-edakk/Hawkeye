# 
# THE TRAINING FOR YOLOv26
# 
# DO NOT RUN UNLESS YOU ARE EXPLICITLY TRAINING THE MODEL
# 

from ultralytics import YOLO

#Load a model
model = YOLO("yolo26n.pt")

#Train the model
results = model.train(data="african-wildlife.yaml", epochs=10, imgsz=640)
