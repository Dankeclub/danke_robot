"""MediaPipe Pose 状态识别: 拉取 RTSP 流，识别站/坐/躺/走，Flask MJPEG 预览。

    python pose_detect.py --rtsp "rtsp://127.0.0.1/live/stream" --port 22400
"""

import argparse
import collections
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template_string
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

_latest_jpeg: bytes | None = None
_latest_state: dict = {"state": "unknown", "confidence": 0.0}
_frame_id: int = 0
_frame_cond = threading.Condition()
_stop_event = threading.Event()

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Pose State Detection</title>
  <style>
    body { margin: 0; background: #111; color: #eee; font-family: system-ui, sans-serif;
           display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    header { padding: 12px 16px; display: flex; justify-content: space-between;
             align-items: center; flex: 0 0 auto; }
    h1 { font-size: 16px; margin: 0; font-weight: 500; }
    #state { font-variant-numeric: tabular-nums; opacity: 0.85; font-size: 14px; }
    img { display: block; flex: 1 1 auto; width: 100%; min-height: 0;
          object-fit: contain; }
  </style>
</head>
<body>
  <header>
    <h1>Pose State Detection</h1>
    <span id="state">--</span>
  </header>
  <img src="/video_feed" alt="live stream">
  <script>
    async function tick() {
      try {
        const r = await fetch('/status');
        const s = await r.json();
        document.getElementById('state').textContent = s.state;
      } catch (_) {}
    }
    setInterval(tick, 1000);
    tick();
  </script>
</body>
</html>
"""

_STATE_LABELS = {
    "standing": "Standing",
    "sitting": "Sitting",
    "lying": "Lying Down",
    "walking": "Walking",
    "unknown": "No Person",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MediaPipe Pose state detection via RTSP")
    p.add_argument("--rtsp", default="rtsp://127.0.0.1/live/stream",
                   help="RTSP stream URL")
    p.add_argument("--port", type=int, default=22400, help="HTTP port")
    p.add_argument("--host", default="0.0.0.0", help="HTTP bind host")
    return p.parse_args()


def calculate_angle(a, b, c) -> float:
    """计算三点构成的角度(度), b 为顶点。"""
    ba = np.array([a.x - b.x, a.y - b.y])
    bc = np.array([c.x - b.x, c.y - b.y])
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))


class StateClassifier:
    """基于关键点几何规则的状态分类器。"""

    def __init__(self, window_size: int = 10):
        self.hip_history: collections.deque = collections.deque(maxlen=window_size)

    def classify(self, landmarks) -> str:
        lm = landmarks.landmark

        l_shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_hip = lm[mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = lm[mp_pose.PoseLandmark.RIGHT_HIP]
        l_knee = lm[mp_pose.PoseLandmark.LEFT_KNEE]
        r_knee = lm[mp_pose.PoseLandmark.RIGHT_KNEE]
        l_ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE]
        r_ankle = lm[mp_pose.PoseLandmark.RIGHT_ANKLE]

        shoulder_y = (l_shoulder.y + r_shoulder.y) / 2
        hip_y = (l_hip.y + r_hip.y) / 2
        knee_y = (l_knee.y + r_knee.y) / 2
        hip_x = (l_hip.x + r_hip.x) / 2

        self.hip_history.append(hip_x)

        # 躺下: 肩/臀/膝 y 坐标差很小(身体水平)
        y_range = max(shoulder_y, hip_y, knee_y) - min(shoulder_y, hip_y, knee_y)
        if y_range < 0.15:
            return "lying"

        # 坐着: 臀-膝角度接近水平,肩明显高于臀
        hip_knee_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        if hip_knee_angle < 120 and shoulder_y < hip_y - 0.05:
            return "sitting"

        # 行走: 髋部 x 位移持续变化
        if len(self.hip_history) >= 8:
            x_displacement = max(self.hip_history) - min(self.hip_history)
            if x_displacement > 0.05:
                ankle_diff = abs(l_ankle.y - r_ankle.y)
                if ankle_diff > 0.02:
                    return "walking"

        return "standing"

def rtsp_capture_thread(rtsp_url: str, frame_holder: dict) -> None:
    """拉流线程: 持续读取 RTSP 帧,断线自动重连。"""
    while not _stop_event.is_set():
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"[WARN] cannot open RTSP: {rtsp_url}, retrying in 3s...")
            time.sleep(3)
            continue

        print(f"[INFO] RTSP connected: {rtsp_url}")
        consec_fail = 0
        while not _stop_event.is_set():
            ok, frame = cap.read()
            if not ok or frame is None:
                consec_fail += 1
                if consec_fail >= 30:
                    print("[WARN] RTSP lost, reconnecting...")
                    break
                time.sleep(0.05)
                continue
            consec_fail = 0
            frame_holder["frame"] = frame

        cap.release()
        if not _stop_event.is_set():
            time.sleep(3)


def publish(jpeg: bytes, state: str, confidence: float) -> None:
    global _latest_jpeg, _latest_state, _frame_id
    with _frame_cond:
        _latest_jpeg = jpeg
        _latest_state = {"state": state, "confidence": round(confidence, 2)}
        _frame_id += 1
        _frame_cond.notify_all()


def processing_loop(frame_holder: dict) -> None:
    """主处理循环: MediaPipe Pose 推理 + 状态分类 + 绘制。"""
    classifier = StateClassifier()
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    while not _stop_event.is_set():
        frame = frame_holder.get("frame")
        if frame is None:
            time.sleep(0.03)
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        annotated = frame.copy()
        state = "unknown"
        confidence = 0.0

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                annotated, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            avg_visibility = np.mean([
                lm.visibility for lm in results.pose_landmarks.landmark])
            confidence = float(avg_visibility)

            if confidence >= 0.5:
                state = classifier.classify(results.pose_landmarks)
            else:
                state = "unknown"

        label = _STATE_LABELS.get(state, state)
        color = (0, 255, 0) if state != "unknown" else (0, 0, 255)
        cv2.putText(annotated, label, (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            publish(buf.tobytes(), state, confidence)

        time.sleep(0.01)

    pose.close()

def mjpeg_generator():
    boundary = b"--frame"
    last_id = -1
    while not _stop_event.is_set():
        with _frame_cond:
            _frame_cond.wait_for(
                lambda: _frame_id != last_id or _stop_event.is_set(),
                timeout=5.0,
            )
            if _stop_event.is_set():
                return
            jpeg = _latest_jpeg
            last_id = _frame_id
        if jpeg:
            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                + jpeg + b"\r\n"
            )


app = Flask(__name__)


@app.route("/")
def index():
    return render_template_string(_INDEX_HTML)


@app.route("/video_feed")
def video_feed():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=--frame",
    )


@app.route("/status")
def status():
    return jsonify(_latest_state)


def main():
    args = parse_args()

    frame_holder: dict = {"frame": None}

    cap_thread = threading.Thread(
        target=rtsp_capture_thread,
        args=(args.rtsp, frame_holder),
        name="RTSPCapture",
        daemon=True,
    )
    cap_thread.start()

    proc_thread = threading.Thread(
        target=processing_loop,
        args=(frame_holder,),
        name="PoseProcessing",
        daemon=True,
    )
    proc_thread.start()

    print(f"[INFO] starting HTTP server on {args.host}:{args.port}")
    print(f"[INFO] RTSP source: {args.rtsp}")
    try:
        app.run(host=args.host, port=args.port, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n[INFO] shutting down...")
    finally:
        _stop_event.set()
        with _frame_cond:
            _frame_cond.notify_all()


if __name__ == "__main__":
    main()
