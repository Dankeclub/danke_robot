import math

import pytest

from behavioral import features as F


def _pose(visibility=0.9, shoulder_y=0.3, hip_y=0.6, lean_dx=0.0):
    """合成一个 33 关键点的 pose dict, 只填测试用到的位点。"""
    lms = [{"x": 0.5, "y": 0.5, "z": 0.0, "visibility": visibility}
           for _ in range(33)]
    # 11=L_SHOULDER, 12=R_SHOULDER, 23=L_HIP, 24=R_HIP
    lms[11] = {"x": 0.45 + lean_dx, "y": shoulder_y, "z": 0, "visibility": 1.0}
    lms[12] = {"x": 0.55 + lean_dx, "y": shoulder_y, "z": 0, "visibility": 1.0}
    lms[23] = {"x": 0.45, "y": hip_y, "z": 0, "visibility": 1.0}
    lms[24] = {"x": 0.55, "y": hip_y, "z": 0, "visibility": 1.0}
    return {"landmarks": lms, "avg_visibility": visibility}


def test_torso_lean_none_when_pose_missing():
    assert F.compute_torso_lean(None) is None


def test_torso_lean_zero_when_upright():
    assert F.compute_torso_lean(_pose(lean_dx=0.0)) == pytest.approx(0.0, abs=0.1)


def test_torso_lean_positive_when_leaning_forward():
    # 肩中点 x 比臀中点 x 大 -> 前倾
    lean = F.compute_torso_lean(_pose(lean_dx=0.05))
    assert lean > 3.0


def test_obj_in_hand_returns_class_when_iou_overlaps():
    objects = [{
        "class_name": "book", "confidence": 0.8,
        "bbox": (0.4, 0.4, 0.6, 0.6),
    }]
    wrists = [(0.5, 0.5)]
    assert F.compute_obj_in_hand_roi(objects, wrists) == "book"


def test_obj_in_hand_returns_none_when_far():
    objects = [{
        "class_name": "book", "confidence": 0.8,
        "bbox": (0.0, 0.0, 0.1, 0.1),
    }]
    wrists = [(0.9, 0.9)]
    assert F.compute_obj_in_hand_roi(objects, wrists) is None


def test_obj_facing_picks_object_inside_gaze_cone():
    objects = [{
        "class_name": "laptop", "confidence": 0.9,
        "bbox": (0.4, 0.4, 0.6, 0.6),
    }]
    assert F.compute_obj_facing(objects, gaze=(0.5, 0.5)) == "laptop"


def test_obj_facing_none_when_no_gaze():
    assert F.compute_obj_facing([], gaze=None) is None


def test_build_frame_marks_person_false_when_no_pose():
    f = F.build_frame(ts=1.0, pose=None, hands={"wrists": [], "motion_hz": 0.0},
                       face=None, objects=[])
    assert f.person_detected is False
    assert f.head_pitch is None
    assert f.hand_motion_hz == 0.0


def test_build_frame_marks_person_true_when_pose_present():
    f = F.build_frame(
        ts=1.0,
        pose=_pose(),
        hands={"wrists": [(0.5, 0.5)], "motion_hz": 1.2},
        face={"head_pitch": 25.0, "head_yaw": 0.0, "gaze_dir": (0.5, 0.5)},
        objects=[],
    )
    assert f.person_detected is True
    assert f.head_pitch == 25.0
    assert f.hand_motion_hz == 1.2
