import cv2
from ultralytics import YOLO
from pathlib import Path
import sys

# python finds database folder from CNN folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.supabase_client import insert_detection

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR/"runs/detect/train4/weights/best.pt"

model = YOLO(MODEL_PATH) #model object
cap = cv2.VideoCapture(0) #open laptop camera

last_logged = None # tracks the last seen animal
frame_id = 0
num_frames = 30 # check every 30 frames

print("==================================")
print("  Drone Animal Detection System   ")
print("  Version 1.0                     ")
print("  Initializing...                 ")
print("==================================")

if not cap.isOpened(): 
    print("  Status: Camera FAILED")
    exit()

print("  Status: Camera OK")
print("  Database: Connected")
print("==================================")

while True:
    ret, frame = cap.read() #capture frame
    if not ret:
        break

    results = model(frame, conf=0.2, verbose=False) 
 
    annotated = results[0].plot()
    cv2.imshow("Live Feed", annotated)

    frame_id += 1

    if frame_id % num_frames == 0: # only log to supabase every num_frames frames
        for box in results[0].boxes:
            species = model.names[int(box.cls)]
            confidence = float(box.conf)
            if species != last_logged and confidence >= 0.75: # insert new entry if its different species + accurate (im scared of reaching the storage limit)
                insert_detection(species, confidence)
                last_logged = species
                print(f"Detection logged: {species} | Confidence: {confidence:.2f}")

    if cv2.waitKey(1) & 0xFF == ord('q'): #if q pressed, exit loop
        break

#Close camera
cap.release()
cv2.destroyAllWindows()