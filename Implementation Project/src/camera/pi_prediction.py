import cv2
from ultralytics import YOLO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "CNN" / "runs/detect/train4/weights/best.pt"

model = YOLO(MODEL_PATH)

PI_IP = "10.0.0.21"
cap = cv2.VideoCapture(f"http://{PI_IP}:5000/video_feed")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Lost connection to Pi stream...")
        break

    results = model(frame, conf=0.2)
    annotated = results[0].plot()
    cv2.imshow("Boxing Detection", annotated)

    print(model.names)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()