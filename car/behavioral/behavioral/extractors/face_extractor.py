"""MediaPipe FaceLandmarker: 头部俯仰/偏航 + 双眼瞳孔近似视线。

mediapipe 0.10+ 使用 Tasks API (mp.tasks.vision.FaceLandmarker)。
模型文件: models/face_landmarker.task (478 landmarks 含 468/473 虹膜点)

俯仰: 鼻尖(1) 与下巴(152) 的纵向间距 vs 双耳跨度的反正切。
偏航: 鼻尖 x 相对双耳中点的偏移量, 用比例换算成度数。
视线: 左眼瞳孔(468) 和右眼瞳孔(473) 的平均位置 (归一化屏幕坐标近似)。
注: 这是粗糙近似, 跑通后用真实画面校准, 不引入 PnP。
"""

from __future__ import annotations

import math
import pathlib
import time

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker,
    FaceLandmarkerOptions,
    RunningMode,
)

_DEFAULT_MODEL = (
    pathlib.Path(__file__).parent.parent.parent / "models" / "face_landmarker.task"
)

# landmark 索引 (Tasks API 与 legacy FaceMesh 一致)
_NOSE_TIP = 1
_CHIN = 152
_LEFT_EAR = 234
_RIGHT_EAR = 454
_LEFT_IRIS = 468
_RIGHT_IRIS = 473


class FaceExtractor:
    def __init__(self, model_path: str | pathlib.Path | None = None) -> None:
        path = pathlib.Path(model_path) if model_path else _DEFAULT_MODEL
        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(path)),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)

    def extract(self, frame_bgr: np.ndarray) -> dict | None:
        ts_ms = int(time.time() * 1000)
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, ts_ms)

        if not result.face_landmarks:
            return None

        lms = result.face_landmarks[0]

        if len(lms) < 478:
            # 模型不含虹膜点,降级用画面中心
            left_iris_x, left_iris_y = 0.5, 0.5
            right_iris_x, right_iris_y = 0.5, 0.5
        else:
            left_iris_x = lms[_LEFT_IRIS].x
            left_iris_y = lms[_LEFT_IRIS].y
            right_iris_x = lms[_RIGHT_IRIS].x
            right_iris_y = lms[_RIGHT_IRIS].y

        nose = lms[_NOSE_TIP]
        chin = lms[_CHIN]
        left_ear = lms[_LEFT_EAR]
        right_ear = lms[_RIGHT_EAR]

        ear_mid_x = (left_ear.x + right_ear.x) / 2.0
        ear_span = max(abs(right_ear.x - left_ear.x), 1e-6)

        pitch = math.degrees(math.atan2(chin.y - nose.y, ear_span))
        pitch -= 45.0  # 中性正脸下 atan2 ≈ 45°, 减去使正脸 ≈ 0°
        yaw = math.degrees(math.atan2(nose.x - ear_mid_x, ear_span / 2.0))

        gaze = (
            (left_iris_x + right_iris_x) / 2.0,
            (left_iris_y + right_iris_y) / 2.0,
        )
        return {"head_pitch": pitch, "head_yaw": yaw, "gaze_dir": gaze}

    def close(self) -> None:
        self._landmarker.close()
