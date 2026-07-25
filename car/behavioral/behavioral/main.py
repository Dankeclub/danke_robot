"""启动入口: 解析参数, 组装 RTSPSource + Pipeline + Server。"""

from __future__ import annotations

import argparse

from .pipeline import Pipeline
from .rtsp_source import RTSPSource
from .server import Server


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Behavioral realtime recognition")
    p.add_argument("--rtsp", required=True, help="RTSP stream URL")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=22400)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    source = RTSPSource(args.rtsp)
    server = Server(source)
    pipeline = Pipeline(
        source=source,
        on_event=server.on_event,
        on_status=server.on_status,
    )
    server.attach(pipeline)

    source.start()
    pipeline.start()
    print(f"[INFO] starting HTTP on {args.host}:{args.port}")
    print(f"[INFO] RTSP source: {args.rtsp}")
    try:
        server.run(args.host, args.port)
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
        source.stop()


if __name__ == "__main__":
    main()
