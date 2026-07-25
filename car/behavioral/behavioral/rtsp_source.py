"""RTSP 拉流线程: 持续读取帧, 缓存最新一帧, 断线自动重连。

迁移自 legacy/pose_detect_v1.py 的 rtsp_capture_thread, 改成类形式以便
被多个消费者(管线 + /preview MJPEG)共享。

注: cv2.VideoCapture 在 FFMPEG 后端对无效 RTSP 地址会阻塞约 30s 才超时,
stop() 的 join(timeout=5) 在此期间会提前返回; daemon 线程随主进程退出
不泄漏。如需提前中断,可在 Task 11 阶段通过 OPENCV_FFMPEG_CAPTURE_OPTIONS
调整 stimeout/rw_timeout。
"""

from __future__ import annotations

import threading
import time

import cv2
import numpy as np

from . import config


class RTSPSource:
    def __init__(self, rtsp_url: str) -> None:
        self._url = rtsp_url
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._thread: threading.Thread | None = None
        self._frame_ts: list[float] = []
        self.connected = False

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name="RTSPSource", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def read_latest(self) -> np.ndarray | None:
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    @property
    def fps(self) -> float:
        now = time.time()
        with self._lock:
            recent = [t for t in self._frame_ts if now - t < 2.0]
            self._frame_ts = recent
        return len(recent) / 2.0 if recent else 0.0

    def _run(self) -> None:
        while not self._stop.is_set():
            cap = cv2.VideoCapture(self._url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print(f"[RTSP] cannot open {self._url}, retry in "
                      f"{config.RTSP_RECONNECT_SEC}s")
                self.connected = False
                time.sleep(config.RTSP_RECONNECT_SEC)
                continue
            print(f"[RTSP] connected: {self._url}")
            self.connected = True
            consec_fail = 0
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    consec_fail += 1
                    if consec_fail >= config.RTSP_MAX_CONSEC_FAIL:
                        print("[RTSP] lost stream, reconnecting...")
                        break
                    time.sleep(0.05)
                    continue
                consec_fail = 0
                with self._lock:
                    self._latest = frame
                    self._frame_ts.append(time.time())
            cap.release()
            self.connected = False
            if not self._stop.is_set():
                time.sleep(config.RTSP_RECONNECT_SEC)
