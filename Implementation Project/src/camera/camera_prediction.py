import cv2
from ultralytics import YOLO
from pathlib import Path
from picamera2 import Picamera2

# this is the same code as CNN with edits in camera

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR/"runs/detect/train4/weights/best.pt"

model = YOLO(MODEL_PATH) #model object
#cap = cv2.VideoCapture(0) #open laptop camera

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
picam2.start()

# if not cap.isOpened(): 
#     print("Camera cannot be opened...")
#     exit()

while True:
    #ret, frame = cap.read() #capture frame
    frame = picam2.capture_array()
    # if not ret:
    #     break

    results = model(frame, conf=0.2) 

    annotated = results[0].plot()
    cv2.imshow("Live Feed", annotated)

    print(model.names)
    if cv2.waitKey(1) & 0xFF == ord('q'): #if q pressed, exit loop
        break

#Close camera
#cap.release()
picam2.stop()
cv2.destroyAllWindows()
