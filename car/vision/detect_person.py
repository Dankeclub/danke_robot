"""USB camera + YOLOv8n person detection, streamed as MJPEG over HTTP.

Run on a Raspberry Pi 5 (or any Linux host with /dev/video0) and open
http://<host>:<port>/ in a browser to view the annotated stream. No local
display, no X11 - works fine over plain SSH.

    python detect_person.py --port 8000
"""

import argparse
import collections
import sys
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template_string
from ultralytics import YOLO


# Shared state between capture thread (producer) and HTTP generators (consumers).
_latest_jpeg: bytes | None = None
_latest_stats: dict = {"fps": 0.0, "persons": 0}
_frame_id: int = 0
_frame_cond = threading.Condition()
_stop_event = threading.Event()
_FALLBACK_JPEG: bytes = b""


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>YOLOv8n person detect</title>
  <style>
    body { margin: 0; background: #111; color: #eee; font-family: system-ui, sans-serif;
           display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    header { padding: 12px 16px; display: flex; justify-content: space-between;
             align-items: center; flex: 0 0 auto; }
    h1 { font-size: 16px; margin: 0; font-weight: 500; }
    #stats { font-variant-numeric: tabular-nums; opacity: 0.85; }
    img { display: block; flex: 1 1 auto; width: 100%; min-height: 0;
          object-fit: contain; image-rendering: pixelated; }
  </style>
</head>
<body>
  <header>
    <h1>YOLOv8n person detect</h1>
    <span id="stats">--</span>
  </header>
  <img src="/video_feed" alt="live stream">
  <script>
    async function tick() {
      try {
        const r = await fetch('/stats');
        const s = await r.json();
        document.getElementById('stats').textContent =
          'FPS ' + s.fps.toFixed(2) + '  |  persons ' + s.persons;
      } catch (_) {}
    }
    setInterval(tick, 1000);
    tick();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="USB camera + YOLOv8n person detection (MJPEG stream)")
    p.add_argument("--source", default="/dev/video0", help="camera device path or index")
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--imgsz", type=int, default=320, help="YOLO inference size")
    p.add_argument("--conf", type=float, default=0.4, help="confidence threshold")
    p.add_argument("--model", default="yolov8n.pt")
    p.add_argument("--host", default="0.0.0.0", help="HTTP bind host")
    p.add_argument("--port", type=int, default=8000, help="HTTP port")
    p.add_argument("--jpeg-quality", type=int, default=80, help="JPEG quality 1-100")
    p.add_argument("--no-overlay", action="store_true", help="disable FPS/persons HUD text")
    p.add_argument("--rotate", type=int, default=180, choices=[0, 90, 180, 270],
                   help="rotate frame N degrees clockwise before inference")
    p.add_argument("--detect-every", type=int, default=2,
                   help="run YOLO every N frames, reuse boxes in between")
    return p.parse_args()


def open_camera(source: str, width: int, height: int) -> cv2.VideoCapture:
    # On Linux, force V4L2 backend so OpenCV doesn't silently fall back to GStreamer.
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
    if not cap.isOpened():
        sys.exit(
            f"[ERROR] cannot open camera {source!r}. "
            f"Check that the device exists, is not used by another process, "
            f"and that the current user is in the 'video' group."
        )
    # MJPG decoding keeps USB bandwidth manageable at 640x480+.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap
def encode_jpeg(frame: np.ndarray, quality: int) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    return buf.tobytes() if ok else b""


def _draw_hud(frame: np.ndarray, fps: float, persons: int) -> None:
    cv2.putText(
        frame,
        f"FPS {fps:5.2f}  persons {persons}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )


def _publish(jpeg: bytes, fps: float, persons: int) -> None:
    global _latest_jpeg, _latest_stats, _frame_id
    with _frame_cond:
        _latest_jpeg = jpeg
        _latest_stats = {"fps": round(fps, 2), "persons": int(persons)}
        _frame_id += 1
        _frame_cond.notify_all()


def _build_fallback_jpeg(width: int, height: int) -> bytes:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (32, 32, 160)  # BGR dark red
    cv2.putText(img, "no signal", (max(10, width // 2 - 110), height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    return encode_jpeg(img, 60)


def capture_loop(args: argparse.Namespace, model: YOLO) -> None:
    """Producer: read frames, run YOLO, encode JPEG, publish shared state."""
    print(f"[INFO] opening camera {args.source} @ {args.width}x{args.height}")
    cap = open_camera(args.source, args.width, args.height)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] camera reports {actual_w}x{actual_h}")

    # Cold-start warmup: first predict() compiles kernels (~2-3s on Pi).
    try:
        model.predict(np.zeros((args.height, args.width, 3), dtype=np.uint8),
                      imgsz=args.imgsz, conf=args.conf, classes=[0], verbose=False)
    except Exception as exc:
        print(f"[WARN] warmup predict failed: {exc}")

    frame_times: collections.deque = collections.deque(maxlen=30)
    consec_fail = 0
    frame_counter = 0
    last_boxes: np.ndarray | None = None
    last_person_count = 0
    try:
        while not _stop_event.is_set():
            t0 = time.monotonic()
            ok, frame = cap.read()
            if not ok or frame is None:
                consec_fail += 1
                if consec_fail >= 150:
                    print("[ERROR] camera lost for 150 frames, publishing fallback and exiting capture loop")
                    _publish(_FALLBACK_JPEG, 0.0, 0)
                    break
                if consec_fail >= 30:
                    time.sleep(0.5)
                continue
            consec_fail = 0

            # 🌟 [在这里新增这一行] 进行水平翻转（左右镜像翻转）
            cv2.flip(frame, 1, dst=frame)
            
            if args.rotate == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif args.rotate == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif args.rotate == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            run_detect = (frame_counter % args.detect_every == 0)
            frame_counter += 1

            if run_detect:
                results = model.predict(
                    frame,
                    imgsz=args.imgsz,
                    conf=args.conf,
                    classes=[0],
                    verbose=False,
                )
                result = results[0]
                last_boxes = result.boxes.xyxy.cpu().numpy() if len(result.boxes) else None
                last_person_count = len(result.boxes)
                annotated = result.plot()
            else:
                annotated = frame.copy()
                if last_boxes is not None:
                    for box in last_boxes:
                        x1, y1, x2, y2 = box[:4].astype(int)
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

            person_count = last_person_count

            frame_times.append(time.monotonic() - t0)
            avg = sum(frame_times) / len(frame_times)
            fps = 1.0 / avg if avg > 0 else 0.0

            if not args.no_overlay:
                _draw_hud(annotated, fps, person_count)

            jpeg = encode_jpeg(annotated, args.jpeg_quality)
            if jpeg:
                _publish(jpeg, fps, person_count)
    finally:
        cap.release()
        print("[INFO] capture loop exited, camera released")


def mjpeg_generator():
    boundary = b"--frame"
    last_id = -1
    while not _stop_event.is_set():
        with _frame_cond:
            got = _frame_cond.wait_for(
                lambda: _frame_id != last_id or _stop_event.is_set(),
                timeout=5.0,
            )
            if _stop_event.is_set():
                return
            if got and _latest_jpeg is not None:
                jpeg = _latest_jpeg
                last_id = _frame_id
            else:
                jpeg = _FALLBACK_JPEG
        # yield outside the lock so other consumers aren't blocked.
        yield (
            boundary + b"\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
            + jpeg + b"\r\n"
        )
        # ================= 补全缺失的 Flask 路由与启动入口 =================

app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(_INDEX_HTML)

@app.route("/video_feed")
def video_feed():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=--frame"
    )

@app.route("/stats")
def stats():
    return jsonify(_latest_stats)

def main():
    global _FALLBACK_JPEG
    args = parse_args()
    
    # 初始化断流占位图
    _FALLBACK_JPEG = _build_fallback_jpeg(args.width, args.height)
    
    print(f"[INFO] loading YOLO model: {args.model}...")
    try:
        model = YOLO(args.model)
    except Exception as e:
        sys.exit(f"[ERROR] failed to load YOLO model: {e}")
        
    # 启动摄像头采集与推理线程（生产者）
    t = threading.Thread(
        target=capture_loop, 
        args=(args, model), 
        name="CaptureThread", 
        daemon=True
    )
    t.start()
    
    # 启动 Flask Web 服务（消费者）
    print(f"[INFO] starting HTTP server on {args.host}:{args.port}")
    try:
        app.run(host=args.host, port=args.port, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n[INFO] shutting down...")
    finally:
        _stop_event.set()
        with _frame_cond:
            _frame_cond.notify_all()
        t.join(timeout=2.0)

if __name__ == "__main__":
    main()
# __CHUNK_4__
