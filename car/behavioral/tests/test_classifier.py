from behavioral.classifier import Classifier
from behavioral.features import FeatureFrame


def _frame(**kw):
    defaults = dict(
        ts=0.0, person_detected=True, head_pitch=0.0, head_yaw=0.0,
        gaze_dir=(0.5, 0.5), hand_motion_hz=0.0, torso_lean=0.0,
        obj_in_hand_roi=None, obj_facing=None, frame_confidence=0.8,
    )
    defaults.update(kw)
    return FeatureFrame(**defaults)


def test_away_after_five_missing_frames():
    c = Classifier()
    for _ in range(4):
        assert c.classify(_frame(person_detected=False)) == "uncertain"
    assert c.classify(_frame(person_detected=False)) == "away"


def test_away_resets_when_person_returns():
    c = Classifier()
    for _ in range(6):
        c.classify(_frame(person_detected=False))
    label = c.classify(_frame(person_detected=True))
    assert label == "uncertain"


def test_reading_rule():
    c = Classifier()
    label = c.classify(_frame(
        head_pitch=25.0, obj_in_hand_roi="book", hand_motion_hz=0.5,
    ))
    assert label == "reading"


def test_reading_rejected_when_no_book():
    c = Classifier()
    assert c.classify(_frame(
        head_pitch=25.0, obj_in_hand_roi=None, hand_motion_hz=0.5,
    )) == "uncertain"


def test_gaming_rule():
    c = Classifier()
    assert c.classify(_frame(
        obj_facing="laptop", hand_motion_hz=2.5, torso_lean=8.0,
    )) == "gaming"


def test_watching_tv_rule():
    c = Classifier()
    assert c.classify(_frame(
        obj_facing="tv", hand_motion_hz=0.2, torso_lean=2.0,
    )) == "watching_tv"


def test_tv_loses_to_gaming_when_hand_high_freq():
    c = Classifier()
    assert c.classify(_frame(
        obj_facing="tv", hand_motion_hz=3.0, torso_lean=8.0,
    )) == "gaming"


def test_uncertain_when_no_rule_matches():
    c = Classifier()
    assert c.classify(_frame()) == "uncertain"
