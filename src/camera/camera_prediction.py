from flask import Flask, Response
from picamera2 import Picamera2
import io
from PIL import Image
#import cv2

app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}
))
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        # need this its in pi
        frame = frame[:, :, ::-1]
        buffer = io.BytesIO()
        Image.fromarray(frame).save(buffer, format='JPEG')
        buffer = buffer.getvalue()
        frame_bytes = buffer
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)