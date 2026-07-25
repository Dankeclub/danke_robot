"""Flask 路由: /healthz /status /events /preview/*。

事件层用一个 threading.Condition 在订阅者之间扇出 SSE 消息。
"""

from __future__ import annotations

import json
import queue
import threading
import time

from flask import Flask, Response, jsonify, render_template_string

from .features import FeatureFrame
from .pipeline import Pipeline
from .rtsp_source import RTSPSource
from .window import WindowResult


_PREVIEW_HTML = """<!doctype html>
<html><head><meta charset='utf-8'><title>Behavioral preview</title>
<style>body{margin:0;background:#111;color:#eee;font-family:system-ui;
display:flex;flex-direction:column;height:100vh}
header{padding:12px 16px;display:flex;justify-content:space-between}
img{flex:1;width:100%;min-height:0;object-fit:contain}</style></head>
<body><header><h1>Behavioral preview</h1><span id='s'>--</span></header>
<img src='/preview/video_feed'>
<script>setInterval(async()=>{const r=await fetch('/status');
document.getElementById('s').textContent=(await r.json()).label;},1000);
</script></body></html>"""


class Server:
    def __init__(self, source: RTSPSource) -> None:
        self._app = Flask(__name__)
        self._source = source
        self._pipeline: Pipeline | None = None
        self._state_lock = threading.Lock()
        self._state = {"label": "uncertain", "confidence": 0.0, "since": None}
        self._subscribers: list[queue.Queue] = []
        self._sub_lock = threading.Lock()
        self._register_routes()

    def attach(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    def on_event(self, result: WindowResult, ff: FeatureFrame) -> None:
        payload = {
            "ts": _iso(ff.ts),
            "label": result.label,
            "previous_label": self._state["label"],
            "confidence": round(result.confidence, 3),
            "window_sec": result.window_sec,
            "features": {
                "head_pitch": ff.head_pitch,
                "hand_motion_hz": ff.hand_motion_hz,
                "obj_in_hand": ff.obj_in_hand_roi,
                "obj_facing": ff.obj_facing,
            },
        }
        with self._sub_lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    pass

    def on_status(self, label: str, conf: float, ff: FeatureFrame) -> None:
        with self._state_lock:
            if label != self._state["label"]:
                self._state["since"] = _iso(ff.ts)
            self._state["label"] = label
            self._state["confidence"] = round(conf, 3)

    def run(self, host: str, port: int) -> None:
        self._app.run(host=host, port=port, threaded=True, debug=False)

    def _register_routes(self) -> None:
        app = self._app

        @app.route("/healthz")
        def healthz():
            return jsonify({
                "status": "ok",
                "rtsp_connected": self._source.connected,
                "fps": round(self._source.fps, 2),
            })

        @app.route("/status")
        def status():
            with self._state_lock:
                return jsonify(dict(self._state))

        @app.route("/events")
        def events():
            q: queue.Queue = queue.Queue(maxsize=32)
            with self._sub_lock:
                self._subscribers.append(q)

            def stream():
                try:
                    while True:
                        payload = q.get()
                        yield f"event: behavior\ndata: {json.dumps(payload)}\n\n"
                finally:
                    with self._sub_lock:
                        if q in self._subscribers:
                            self._subscribers.remove(q)

            return Response(stream(), mimetype="text/event-stream")

        @app.route("/preview")
        def preview():
            return render_template_string(_PREVIEW_HTML)

        @app.route("/preview/video_feed")
        def video_feed():
            return Response(
                _mjpeg(self._pipeline),
                mimetype="multipart/x-mixed-replace; boundary=--frame",
            )


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _mjpeg(pipeline: Pipeline | None):
    while True:
        if pipeline is None:
            time.sleep(0.1)
            continue
        jpeg = pipeline.latest_annotated_frame()
        if jpeg is None:
            time.sleep(0.05)
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n"
               b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
               + jpeg + b"\r\n")
        time.sleep(0.05)
