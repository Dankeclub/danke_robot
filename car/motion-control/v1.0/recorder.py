import asyncio
import json
import os
import time
from datetime import datetime, timezone

import aiofiles

from command_queue import CommandProcessor
import config


class Recorder:
    def __init__(self, command_processor: CommandProcessor, routes_dir: str):
        self.command_processor = command_processor
        self.routes_dir = routes_dir
        self._recording = False
        self._commands: list = []
        self._record_start: float = 0.0
        self._playback_task: asyncio.Task | None = None
        self._playback_paused = False
        self.on_event = None

        os.makedirs(routes_dir, exist_ok=True)

    def start_recording(self):
        self._recording = True
        self._commands = []
        self._record_start = time.monotonic()
        self.command_processor.set_mode("recording")

    def stop_recording(self) -> list:
        self._recording = False
        self.command_processor.set_mode("manual")
        return self._commands

    def record_command(self, vx: float, vy: float, omega: float):
        if not self._recording:
            return
        t = time.monotonic() - self._record_start
        self._commands.append({"t": round(t, 4), "vx": vx, "vy": vy, "omega": omega})

    async def save(self, name: str):
        data = {
            "name": name,
            "type": "recorded",
            "created": datetime.now(timezone.utc).isoformat(),
            "commands": self._commands,
        }
        path = os.path.join(self.routes_dir, f"{name}.json")
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

    async def load(self, name: str) -> dict:
        path = os.path.join(self.routes_dir, f"{name}.json")
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        return json.loads(content)

    async def list_routes(self) -> list:
        routes = []
        if not os.path.exists(self.routes_dir):
            return routes
        for fname in os.listdir(self.routes_dir):
            if fname.endswith(".json"):
                path = os.path.join(self.routes_dir, fname)
                async with aiofiles.open(path, "r") as f:
                    content = await f.read()
                data = json.loads(content)
                routes.append({
                    "name": data.get("name", fname[:-5]),
                    "type": data.get("type", "unknown"),
                    "created": data.get("created", ""),
                })
        return routes

    async def playback(self, name: str):
        data = await self.load(name)
        commands = data.get("commands", [])
        if not commands:
            return

        self.command_processor.set_mode("playback")
        self._playback_paused = False

        try:
            for i, cmd in enumerate(commands):
                if self._playback_task and self._playback_task.cancelled():
                    break

                while self._playback_paused:
                    await asyncio.sleep(0.05)

                self.command_processor.set_command(cmd["vx"], cmd["vy"], cmd["omega"])

                if i < len(commands) - 1:
                    dt = commands[i + 1]["t"] - cmd["t"]
                    await asyncio.sleep(max(dt, 0))

            self.command_processor.stop()
            self.command_processor.set_mode("manual")
            if self.on_event:
                self.on_event("playback_done", {})
        except asyncio.CancelledError:
            self.command_processor.stop()
            self.command_processor.set_mode("manual")

    def start_playback(self, name: str) -> asyncio.Task:
        self._playback_task = asyncio.create_task(self.playback(name))
        return self._playback_task

    def pause_playback(self):
        self._playback_paused = not self._playback_paused

    def stop_playback(self):
        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()
        self.command_processor.stop()
        self.command_processor.set_mode("manual")
