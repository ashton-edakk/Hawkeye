import cv2
from ultralytics import YOLO
from pathlib import Path
import sys

# python finds database folder from CNN folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.supabase_client import insert_detection

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "runs/detect/train4/weights/best.pt"


def print_banner():
    print("----------------------------------------")
    print("|   Drone Animal Detection System      |")
    print("|   Version 2.0                        |")
    print("----------------------------------------")


def print_menu():
    print("\n----------------------------------------")
    print("│              MAIN MENU               │")
    print("|                                      │")
    print("│  [1]  Live Detection (Camera)        │")
    print("│  [2]  View Dashboard (Browser)       │")
    print("│  [Q]  Quit                           │")
    print("----------------------------------------")
    return input("  Select an option: ").strip().lower()


def run_detection():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    frame_id = 0
    num_frames = 30
    logged_ids = set()  # track IDs we've already inserted

    print("\n  Initializing camera >.< ...")

    if not cap.isOpened():
        print("  Camera FAILED, u baka — returning to menu.\n")
        return

    print("  Camera OK")
    print("  Model loaded")
    print("  Database connected")
    print("  [Press Q in the video window to stop]\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(frame, conf=0.2, persist=True, verbose=False)
        annotated = results[0].plot()
        cv2.imshow("Live Feed  |  Press Q to return to menu", annotated)

        frame_id += 1

        if frame_id % num_frames == 0:
            boxes = results[0].boxes
            # .id is None if tracking lost, so guard against it
            if boxes.id is not None:
                for box, track_id in zip(boxes, boxes.id):
                    track_id = int(track_id)
                    species = model.names[int(box.cls)]
                    confidence = float(box.conf)

                    if confidence >= 0.85 and track_id not in logged_ids:
                        logged_ids.add(track_id)
                        if species == "zebra":
                            print(f"  ALERT: ZEBRA DETECTED! (ID {track_id}) | Confidence: {confidence:.2f}")
                        else:
                            insert_detection(species, confidence)
                            print(f"  Detection logged: {species} (ID {track_id}) | Confidence: {confidence:.2f}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("  Camera closed.")


def run_dashboard():
    import subprocess
    dashboard_path = BASE_DIR.parent / "visualization" / "dashboard.py"

    if not dashboard_path.exists():
        print(f"\n  Dashboard not found at: {dashboard_path}")
        print("  Make sure dashboard.py is in the visualization/ folder.\n")
        return

    print("\n  Launching dashboard in browser...")
    print("  (Close the browser tab or press Ctrl+C here to stop)\n")

    try:
        subprocess.run([sys.executable, str(dashboard_path)], check=True)
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
    except subprocess.CalledProcessError as e:
        print(f"\n  ✗ Dashboard exited with error: {e}")


def main():
    print_banner()

    while True:
        choice = print_menu()

        if choice == "1":
            run_detection()
        elif choice == "2":
            run_dashboard()
        elif choice in ("q", "quit", "exit"):
            print("\n  Goodbye.\n")
            break
        else:
            print("  Invalid option. Please choose 1, 2, or Q.")


if __name__ == "__main__":
    main()