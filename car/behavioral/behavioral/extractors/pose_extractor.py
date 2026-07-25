"""MediaPipe Pose 抽取: 33 个身体关键点。

注: mediapipe 0.10+ 移除了 mp.solutions.pose,改用 Tasks API。
模型文件: models/pose_landmarker_lite.task (首次使用前需存在)。
"""

from __future__ import annotations

import pathlib
import time

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

_DEFAULT_MODEL = pathlib.Path(__file__).parent.parent.parent / "models" / "pose_landmarker_lite.task"


class PoseExtractor:
    def __init__(self, model_path: str | pathlib.Path | None = None) -> None:
        path = pathlib.Path(model_path) if model_path else _DEFAULT_MODEL
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(path)),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

    def extract(self, frame_bgr: np.ndarray) -> dict | None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(time.time() * 1000)
        result = self._landmarker.detect_for_video(mp_image, ts_ms)

        if not result.pose_landmarks:
            return None

        lms = [
            {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
            for lm in result.pose_landmarks[0]
        ]
        avg_vis = float(np.mean([lm["visibility"] for lm in lms]))
        return {"landmarks": lms, "avg_visibility": avg_vis}

    def close(self) -> None:
        self._landmarker.close()
