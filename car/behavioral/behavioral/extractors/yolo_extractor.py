"""YOLOv8n 物体检测, 只保留 config 关心的 COCO 类别。"""

from __future__ import annotations

import numpy as np
from ultralytics import YOLO

from .. import config


class YoloExtractor:
    def __init__(self) -> None:
        self._model = YOLO(config.YOLO_MODEL)
        names = self._model.names
        self._keep_ids = {
            i for i, n in names.items() if n in config.YOLO_CLASSES
        }
        self._names = names

    def extract(self, frame_bgr: np.ndarray) -> list[dict]:
        h, w = frame_bgr.shape[:2]
        results = self._model.predict(
            frame_bgr, conf=config.YOLO_CONFIDENCE, verbose=False
        )
        out: list[dict] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.item())
                if cls_id not in self._keep_ids:
                    continue
                conf = float(box.conf.item())
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                out.append({
                    "class_name": self._names[cls_id],
                    "confidence": conf,
                    "bbox": (x1 / w, y1 / h, x2 / w, y2 / h),
                })
        return out
