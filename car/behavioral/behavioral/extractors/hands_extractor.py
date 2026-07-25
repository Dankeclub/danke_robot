"""MediaPipe Hands 抽取 + 手腕运动频率估算。

mediapipe 0.10+ 使用 Tasks API (mp.tasks.vision.HandLandmarker)。
模型文件: models/hand_landmarker.task
"""

from __future__ import annotations

import collections
import math
import pathlib
import time

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

_DEFAULT_MODEL = (
    pathlib.Path(__file__).parent.parent.parent / "models" / "hand_landmarker.task"
)
_MOTION_THRESHOLD = 0.02
_WINDOW_SEC = 2.0

# Tasks API 的 HandLandmark 索引: 手腕 = 0(与 legacy WRIST 一致)
_WRIST_IDX = 0


class HandsExtractor:
    def __init__(self, model_path: str | pathlib.Path | None = None) -> None:
        path = pathlib.Path(model_path) if model_path else _DEFAULT_MODEL
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(path)),
            running_mode=RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._wrist_history: collections.deque = collections.deque()

    def extract(self, frame_bgr: np.ndarray, ts: float) -> dict:
        ts_ms = int(time.time() * 1000)
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, ts_ms)

        wrists: list[tuple[float, float]] = []
        if result.hand_landmarks:
            for hand_lms in result.hand_landmarks:
                w = hand_lms[_WRIST_IDX]
                wrists.append((w.x, w.y))

        self._update_history(wrists, ts)
        return {"wrists": wrists, "motion_hz": self._compute_hz(ts)}

    def _update_history(self, wrists: list[tuple[float, float]], ts: float) -> None:
        if wrists:
            x = sum(w[0] for w in wrists) / len(wrists)
            y = sum(w[1] for w in wrists) / len(wrists)
            self._wrist_history.append((ts, x, y))
        while self._wrist_history and ts - self._wrist_history[0][0] > _WINDOW_SEC:
            self._wrist_history.popleft()

    def _compute_hz(self, ts: float) -> float:
        if len(self._wrist_history) < 2:
            return 0.0
        events = 0
        prev = self._wrist_history[0]
        for cur in list(self._wrist_history)[1:]:
            dx, dy = cur[1] - prev[1], cur[2] - prev[2]
            if math.hypot(dx, dy) > _MOTION_THRESHOLD:
                events += 1
            prev = cur
        return events / _WINDOW_SEC

    def close(self) -> None:
        self._landmarker.close()
