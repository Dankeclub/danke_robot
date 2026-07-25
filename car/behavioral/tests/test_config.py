from behavioral import config


def test_window_constants_match_spec():
    assert config.WINDOW_SEC == 30
    assert config.VOTE_RATIO_MIN == 0.6
    assert config.AVG_CONFIDENCE_MIN == 0.65
    assert config.SWITCH_AGREE_WINDOWS == 2


def test_inference_rate_is_two_fps():
    assert config.INFER_FPS == 2


def test_label_set_is_exactly_five():
    assert set(config.LABELS) == {
        "reading", "gaming", "watching_tv", "uncertain", "away"
    }


def test_yolo_classes_match_spec():
    assert config.YOLO_CLASSES == ["book", "tv", "laptop", "cell phone"]
