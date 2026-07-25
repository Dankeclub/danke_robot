from behavioral.window import WindowVoter, WindowResult


def _feed(voter, count, label, conf=0.8, start_ts=0.0, dt=0.5):
    """连续喂 count 帧, 返回每帧返回的列表(便于断言切换时机)。"""
    out = []
    for i in range(count):
        out.append(voter.push(start_ts + i * dt, label, conf))
    return out


def test_no_emit_before_first_full_window():
    v = WindowVoter()
    # 喂半窗的票, 不应有任何切换输出
    results = _feed(v, count=20, label="reading", start_ts=0.0, dt=0.5)
    assert all(r is None for r in results)


def test_emits_first_label_after_two_agreeing_windows():
    v = WindowVoter()
    # 喂 90 秒的 reading 高置信度票, 确保跨过 2 个窗口
    results = _feed(v, count=180, label="reading", conf=0.9,
                    start_ts=0.0, dt=0.5)
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 1
    assert emitted[0].label == "reading"
    assert emitted[0].confidence >= 0.9 - 1e-6


def test_no_emit_when_confidence_below_threshold():
    v = WindowVoter()
    results = _feed(v, count=180, label="reading", conf=0.4,
                    start_ts=0.0, dt=0.5)
    assert all(r is None for r in results)


def test_sustained_new_label_triggers_switch():
    v = WindowVoter()
    # 先稳定在 reading
    _feed(v, count=180, label="reading", conf=0.9, start_ts=0.0, dt=0.5)
    # 持续 60 秒 gaming, 长到足以让窗口冲走 reading 残留 + 2 个连续 settle 都同意
    results = _feed(v, count=120, label="gaming", conf=0.9,
                    start_ts=90.0, dt=0.5)
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 1
    assert emitted[0].label == "gaming"


def test_brief_flicker_does_not_switch():
    v = WindowVoter()
    # 稳定在 reading
    _feed(v, count=180, label="reading", conf=0.9, start_ts=0.0, dt=0.5)
    # 仅 5 帧 gaming 闪烁(2.5s), 不足以让 gaming 在 30s 窗口中赢
    for i in range(5):
        v.push(90.0 + i * 0.5, "gaming", 0.9)
    # 继续 reading 60s
    tail = _feed(v, count=120, label="reading", conf=0.9,
                 start_ts=92.5, dt=0.5)
    # 不应产生任何切换事件
    assert all(r is None for r in tail)


def test_minority_label_is_ignored():
    v = WindowVoter()
    # 50% reading + 50% uncertain -> 任何一方都达不到 0.6 阈值,不应发布
    for i in range(180):
        label = "reading" if i % 2 == 0 else "uncertain"
        v.push(i * 0.5, label, 0.9)
    # 经过 90s 混合数据后没有任何发布
    # 再走 90s 纯 reading, 应当首次发布 reading
    results = _feed(v, count=180, label="reading", conf=0.9,
                    start_ts=90.0, dt=0.5)
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 1
    assert emitted[0].label == "reading"
