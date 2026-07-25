"""FeatureFrame 数据类 + 各特征的计算函数。

接受 extractors 的原始输出, 组合成单帧特征向量供 classifier 使用。
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FeatureFrame:
    ts: float
    person_detected: bool
    head_pitch: float | None
    head_yaw: float | None
    gaze_dir: tuple[float, float] | None
    hand_motion_hz: float
    torso_lean: float | None
    obj_in_hand_roi: str | None
    obj_facing: str | None
    frame_confidence: float


def compute_torso_lean(pose: dict | None) -> float | None:
    if pose is None:
        return None
    lms = pose["landmarks"]
    shoulder_x = (lms[11]["x"] + lms[12]["x"]) / 2.0
    shoulder_y = (lms[11]["y"] + lms[12]["y"]) / 2.0
    hip_x = (lms[23]["x"] + lms[24]["x"]) / 2.0
    hip_y = (lms[23]["y"] + lms[24]["y"]) / 2.0
    dx = shoulder_x - hip_x
    dy = shoulder_y - hip_y  # 屏幕 y 向下, 肩在臀上方时 dy<0
    if abs(dy) < 1e-6:
        return 0.0
    return math.degrees(math.atan2(dx, -dy))


def _iou(a: tuple[float, float, float, float],
         b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter == 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter + 1e-9)


def compute_obj_in_hand_roi(
    objects: list[dict],
    wrists: list[tuple[float, float]],
    iou_min: float = 0.05,
) -> str | None:
    if not objects or not wrists:
        return None
    best_cls: str | None = None
    best_iou = iou_min
    for wx, wy in wrists:
        roi = (wx - 0.1, wy - 0.1, wx + 0.1, wy + 0.1)
        for obj in objects:
            iou = _iou(roi, obj["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_cls = obj["class_name"]
    return best_cls


def compute_obj_facing(
    objects: list[dict],
    gaze: tuple[float, float] | None,
    cone_radius: float = 0.2,
) -> str | None:
    if gaze is None or not objects:
        return None
    gx, gy = gaze
    best_cls: str | None = None
    best_area = 0.0
    for obj in objects:
        x1, y1, x2, y2 = obj["bbox"]
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if math.hypot(cx - gx, cy - gy) > cone_radius:
            continue
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        if area > best_area:
            best_area = area
            best_cls = obj["class_name"]
    return best_cls


def build_frame(
    ts: float,
    pose: dict | None,
    hands: dict,
    face: dict | None,
    objects: list[dict],
) -> FeatureFrame:
    person = pose is not None
    confidences: list[float] = []
    if pose is not None:
        confidences.append(pose["avg_visibility"])
    if objects:
        confidences.append(max(o["confidence"] for o in objects))
    frame_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return FeatureFrame(
        ts=ts,
        person_detected=person,
        head_pitch=face["head_pitch"] if face else None,
        head_yaw=face["head_yaw"] if face else None,
        gaze_dir=face["gaze_dir"] if face else None,
        hand_motion_hz=hands.get("motion_hz", 0.0),
        torso_lean=compute_torso_lean(pose),
        obj_in_hand_roi=compute_obj_in_hand_roi(objects, hands.get("wrists", [])),
        obj_facing=compute_obj_facing(
            objects, face["gaze_dir"] if face else None
        ),
        frame_confidence=frame_conf,
    )
