import cv2
from ultralytics import YOLO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR/"runs/detect/train/weights/best.pt"

model = YOLO(MODEL_PATH) #model object
cap = cv2.VideoCapture(0) #open laptop camera

if not cap.isOpened(): 
    print("Camera cannot be opened...")
    exit()

while True:
    ret, frame = cap.read() #capture frame
    if not ret:
        break
    
    results = model(frame, conf=0.01)
    #results = model(frame, conf=0.01) 

    annotated = results[0].plot()
    cv2.imshow("Live Feed", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'): #if q pressed, exit loop
        break

#Close camera
cap.release()
cv2.destroyAllWindows()
