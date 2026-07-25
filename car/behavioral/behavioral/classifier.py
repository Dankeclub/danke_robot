"""单帧 FeatureFrame -> 5 标签之一。规则严格按 spec §分类规则 实现。"""

from __future__ import annotations

from . import config
from .features import FeatureFrame


class Classifier:
    def __init__(self) -> None:
        self._missing_streak = 0

    def classify(self, frame: FeatureFrame) -> str:
        if not frame.person_detected:
            self._missing_streak += 1
            if self._missing_streak >= config.AWAY_MISSING_FRAMES:
                return "away"
            return "uncertain"
        self._missing_streak = 0

        if self._is_gaming(frame):
            return "gaming"
        if self._is_watching_tv(frame):
            return "watching_tv"
        if self._is_reading(frame):
            return "reading"
        return "uncertain"

    @staticmethod
    def _is_reading(f: FeatureFrame) -> bool:
        if f.head_pitch is None:
            return False
        lo, hi = config.HEAD_PITCH_READING
        return (
            lo <= f.head_pitch <= hi
            and f.obj_in_hand_roi == "book"
            and f.hand_motion_hz < config.HAND_MOTION_HZ_READING
        )

    @staticmethod
    def _is_gaming(f: FeatureFrame) -> bool:
        return (
            f.obj_facing in ("tv", "laptop", "cell phone")
            and f.hand_motion_hz >= config.HAND_MOTION_HZ_GAMING
            and (f.torso_lean or 0.0) > config.TORSO_LEAN_FORWARD
        )

    @staticmethod
    def _is_watching_tv(f: FeatureFrame) -> bool:
        return (
            f.obj_facing in ("tv", "laptop")
            and f.hand_motion_hz < config.HAND_MOTION_HZ_TV
            and (f.torso_lean or 0.0) <= config.TORSO_LEAN_FORWARD
        )
