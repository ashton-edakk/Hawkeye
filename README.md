# Hawkeye: Drone System to Monitor Animals

This folder contains the implementation artifacts for the Hawkeye prototype, including source code, implementation documentation, reports, and presentation materials.

## What Is In This Folder

### Implementation documents
- `HawkeyeFinalReport.pdf`  
  Final Hawkeye report (deliverables, testing, inspection, conclusions, issues).
- `HawkeyeSummary.pdf`  
  Short summary document.
- `HawkeyePresentation.pptx`  
  Hawkeye presentation deck.

### Source code
- `src/CNN/yolo_prediction.py`  
  Main YOLO detection app with menu flow and detection logging.
- `src/CNN/yolo_training.py`  
  Roboflow + YOLOv26 training script.
- `src/database/supabase_client.py`  
  Supabase client initialization and insert helper.
- `src/camera/camera_prediction.py`  
  Flask MJPEG stream server for Raspberry Pi camera feed.
- `src/camera/pi_prediction.py`  
  Detection client that consumes the Pi MJPEG feed and performs logging/tracking.

## Current Runtime Flow

### Laptop/local camera detection
- Entry point: `src/CNN/yolo_prediction.py`
- Loads model from `src/CNN/runs/detect/train4/weights/best.pt`
- Runs YOLO tracking and logs detections above confidence threshold
- Uses unique track IDs to reduce duplicate inserts

### Raspberry Pi streaming + detection path
1. Start stream server on Pi:
   - `src/camera/camera_prediction.py`
   - Serves MJPEG at `/video_feed` on port `5000`
2. Run detector client:
   - `src/camera/pi_prediction.py`
   - Connects to Pi stream (`http://<PI_IP>:5000/video_feed`)
   - Runs YOLO + tracking + Supabase inserts

## Dependencies

Declared in `requirements.txt`:
- `opencv-python`
- `ultralytics`
- `numpy`
- `pandas`
- `sqlalchemy`
- `requests`

Also used by source:
- `supabase`
- `python-dotenv`
- `flask`
- `pillow`
- `roboflow` (training script)
- `picamera2` (Pi camera streaming script)

Install baseline:

```bash
pip install -r requirements.txt
pip install supabase python-dotenv flask pillow roboflow picamera2
```

## Environment Configuration

Create `src/CNN/.env`:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
```

`src/database/supabase_client.py` reads this file to initialize Supabase.

## Typical Run Commands

From `Hawkeye/`:

```bash
python src/CNN/yolo_prediction.py
```

For Pi stream server:

```bash
python src/camera/camera_prediction.py
```

For Pi detection client:

```bash
python src/camera/pi_prediction.py
```