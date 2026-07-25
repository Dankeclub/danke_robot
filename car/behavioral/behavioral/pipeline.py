"""把 source + extractors + features + classifier + window 串成单循环。

抽帧节奏由 INFER_FPS 控制 (默认 2 fps), 每次循环:
  1. 从 source 拿最新帧
  2. 跑 4 个 extractor
  3. 合成 FeatureFrame
  4. classifier -> 单帧标签
  5. window.push -> 若返回 WindowResult, 触发 on_event
  6. 绘制标注帧供 /preview/video_feed 消费
"""

from __future__ import annotations

import threading
import time
from typing import Callable

import cv2
import numpy as np

from . import config
from .classifier import Classifier
from .extractors.face_extractor import FaceExtractor
from .extractors.hands_extractor import HandsExtractor
from .extractors.pose_extractor import PoseExtractor
from .extractors.yolo_extractor import YoloExtractor
from .features import FeatureFrame, build_frame
from .rtsp_source import RTSPSource
from .window import WindowResult, WindowVoter


EventCB = Callable[[WindowResult, FeatureFrame], None]
StatusCB = Callable[[str, float, FeatureFrame], None]


class Pipeline:
    def __init__(self, source: RTSPSource, on_event: EventCB,
                 on_status: StatusCB) -> None:
        self._source = source
        self._on_event = on_event
        self._on_status = on_status
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._jpeg_lock = threading.Lock()
        self._latest_jpeg: bytes | None = None

        self._pose = PoseExtractor()
        self._hands = HandsExtractor()
        self._face = FaceExtractor()
        self._yolo = YoloExtractor()
        self._classifier = Classifier()
        self._voter = WindowVoter()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name="Pipeline", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._pose.close()
        self._hands.close()
        self._face.close()

    def latest_annotated_frame(self) -> bytes | None:
        with self._jpeg_lock:
            return self._latest_jpeg

    def _run(self) -> None:
        interval = 1.0 / config.INFER_FPS
        while not self._stop.is_set():
            t0 = time.time()
            frame = self._source.read_latest()
            if frame is None:
                time.sleep(0.1)
                continue
            ts = time.time()
            pose = self._pose.extract(frame)
            hands = self._hands.extract(frame, ts)
            face = self._face.extract(frame)
            objects = self._yolo.extract(frame)
            ff = build_frame(ts, pose, hands, face, objects)
            label = self._classifier.classify(ff)
            self._on_status(label, ff.frame_confidence, ff)
            result = self._voter.push(ts, label, ff.frame_confidence)
            if result is not None:
                self._on_event(result, ff)
            self._publish_preview(frame, label, ff)
            elapsed = time.time() - t0
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    def _publish_preview(self, frame: np.ndarray, label: str,
                          ff: FeatureFrame) -> None:
        annotated = frame.copy()
        color = (0, 255, 0) if label not in ("uncertain", "away") else (0, 0, 255)
        cv2.putText(annotated, label, (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        hud = f"pitch={ff.head_pitch:.0f} hz={ff.hand_motion_hz:.1f}" \
              if ff.head_pitch is not None else "no face"
        cv2.putText(annotated, hud, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            with self._jpeg_lock:
                self._latest_jpeg = buf.tobytes()
