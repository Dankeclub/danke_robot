"""滑动窗口投票 + 状态平滑。

每秒结算一次, 票来源于 classifier 的单帧标签。
"""

from __future__ import annotations

import collections
from dataclasses import dataclass

from . import config


@dataclass
class WindowResult:
    label: str
    confidence: float
    window_sec: int


class WindowVoter:
    def __init__(self) -> None:
        self._votes: collections.deque = collections.deque()  # (ts, label, conf)
        self._last_settle_sec: int | None = None
        self._published_label: str | None = None
        self._candidate_label: str | None = None
        self._candidate_agree_count = 0

    def push(self, ts: float, label: str, confidence: float
             ) -> WindowResult | None:
        self._votes.append((ts, label, confidence))
        cutoff = ts - config.WINDOW_SEC
        while self._votes and self._votes[0][0] < cutoff:
            self._votes.popleft()

        current_sec = int(ts)
        if self._last_settle_sec is not None and current_sec == self._last_settle_sec:
            return None
        if ts < config.WINDOW_SEC:
            self._last_settle_sec = current_sec
            return None
        self._last_settle_sec = current_sec

        return self._settle()

    def _settle(self) -> WindowResult | None:
        if not self._votes:
            return None
        counter: dict[str, list[float]] = {}
        for _ts, lbl, conf in self._votes:
            counter.setdefault(lbl, []).append(conf)
        total = len(self._votes)
        best_label, best_confs = max(counter.items(), key=lambda kv: len(kv[1]))
        ratio = len(best_confs) / total
        avg_conf = sum(best_confs) / len(best_confs)

        if ratio < config.VOTE_RATIO_MIN or avg_conf < config.AVG_CONFIDENCE_MIN:
            self._candidate_label = None
            self._candidate_agree_count = 0
            return None

        if best_label == self._published_label:
            return None

        if self._candidate_label == best_label:
            self._candidate_agree_count += 1
        else:
            self._candidate_label = best_label
            self._candidate_agree_count = 1

        if self._candidate_agree_count >= config.SWITCH_AGREE_WINDOWS:
            self._published_label = best_label
            self._candidate_label = None
            self._candidate_agree_count = 0
            return WindowResult(
                label=best_label,
                confidence=avg_conf,
                window_sec=config.WINDOW_SEC,
            )
        return None
