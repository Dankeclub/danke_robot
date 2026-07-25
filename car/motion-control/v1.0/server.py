import asyncio
import json
import time

from aiohttp import web

from controller import AsyncRobotController
from odometry import Odometry
from command_queue import CommandProcessor
from recorder import Recorder
from navigator import Navigator
import config


class RobotApp:
    def __init__(self):
        self.controller = AsyncRobotController()
        self.odometry = Odometry(config.MAX_SPEED_MPS, config.MAX_OMEGA_RPS)
        self.command_processor = CommandProcessor(self.controller, self.odometry)
        self.recorder = Recorder(self.command_processor, config.ROUTES_DIR)
        self.navigator = Navigator(self.command_processor, self.odometry)

        self.control_ws = None
        self.observers: set = set()
        self._tasks: list = []

        self.recorder.on_event = self._broadcast_event
        self.navigator.on_event = self._broadcast_event

    async def start_background_tasks(self, app):
        self._tasks.append(asyncio.create_task(self.command_processor.run()))
        self._tasks.append(asyncio.create_task(self._state_broadcast()))

    async def cleanup(self, app):
        self.command_processor.shutdown()
        for task in self._tasks:
            task.cancel()
        await self.controller.stop()

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=config.WS_HEARTBEAT)
        await ws.prepare(request)

        is_controller = False
        if self.control_ws is None:
            self.control_ws = ws
            is_controller = True
        else:
            self.observers.add(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_message(ws, msg.data, is_controller)
        finally:
            if is_controller:
                self.control_ws = None
                self.command_processor.stop()
                if self.observers:
                    new_controller = self.observers.pop()
                    self.control_ws = new_controller
            else:
                self.observers.discard(ws)

        return ws

    async def _handle_message(self, ws, data: str, is_controller: bool):
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type")

        if not is_controller and msg_type in ("move", "stop", "record", "playback", "navigate"):
            await ws.send_json({"type": "event", "event": "error", "data": {"msg": "observer cannot send commands"}})
            return

        if msg_type == "move":
            vx = float(msg.get("vx", 0))
            vy = float(msg.get("vy", 0))
            omega = float(msg.get("omega", 0))
            if self.command_processor.get_mode() == "navigating":
                self.navigator.stop()
            self.command_processor.set_command(vx, vy, omega)
            if self.command_processor.get_mode() == "recording":
                self.recorder.record_command(vx, vy, omega)

        elif msg_type == "stop":
            if self.command_processor.get_mode() == "navigating":
                self.navigator.stop()
            self.command_processor.stop()

        elif msg_type == "calibrate_pose":
            self.odometry.calibrate(
                float(msg.get("x", 0)),
                float(msg.get("y", 0)),
                float(msg.get("theta", 0)),
            )

        elif msg_type == "reset_odometry":
            self.odometry.reset()

        elif msg_type == "record":
            action = msg.get("action")
            if action == "start":
                self.recorder.start_recording()
            elif action == "stop":
                self.recorder.stop_recording()
            elif action == "save":
                name = msg.get("name", "unnamed")
                await self.recorder.save(name)

        elif msg_type == "playback":
            action = msg.get("action")
            if action == "start":
                name = msg.get("name", "")
                self.recorder.start_playback(name)
            elif action == "pause":
                self.recorder.pause_playback()
            elif action == "stop":
                self.recorder.stop_playback()

        elif msg_type == "navigate":
            waypoints = msg.get("waypoints", [])
            if waypoints:
                self.navigator.start(waypoints)

        elif msg_type == "list_routes":
            routes = await self.recorder.list_routes()
            await ws.send_json({"type": "routes_list", "routes": routes})

    async def _state_broadcast(self):
        while True:
            state = {
                "type": "state",
                "ts": time.time(),
                "pose": self.odometry.get_pose(),
                "velocity": {
                    "vx": self.command_processor.vx,
                    "vy": self.command_processor.vy,
                    "omega": self.command_processor.omega,
                },
                "mode": self.command_processor.get_mode(),
                "motors": dict(zip(
                    ("m1", "m2", "m3", "m4"),
                    self.command_processor.get_motor_values(),
                )),
            }
            payload = json.dumps(state)

            all_ws = []
            if self.control_ws:
                all_ws.append(self.control_ws)
            all_ws.extend(self.observers)

            for ws in all_ws:
                if not ws.closed:
                    try:
                        await ws.send_str(payload)
                    except Exception:
                        pass

            await asyncio.sleep(config.STATE_BROADCAST_INTERVAL)

    def _broadcast_event(self, event: str, data: dict):
        msg = json.dumps({"type": "event", "event": event, "data": data})
        all_ws = []
        if self.control_ws:
            all_ws.append(self.control_ws)
        all_ws.extend(self.observers)

        for ws in all_ws:
            if not ws.closed:
                asyncio.create_task(ws.send_str(msg))

    def create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/ws", self.ws_handler)
        app.router.add_static("/", "static", show_index=True)
        app.on_startup.append(self.start_background_tasks)
        app.on_cleanup.append(self.cleanup)
        return app


if __name__ == "__main__":
    robot_app = RobotApp()
    web.run_app(robot_app.create_app(), host=config.SERVER_HOST, port=config.SERVER_PORT)
