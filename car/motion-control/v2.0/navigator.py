import asyncio
import math

from command_queue import CommandProcessor
from odometry import Odometry
import config


def normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


class Navigator:
    def __init__(self, command_processor: CommandProcessor, odometry: Odometry):
        self.command_processor = command_processor
        self.odometry = odometry
        self._task: asyncio.Task | None = None
        self.on_event = None

    async def navigate(self, waypoints: list):
        self.command_processor.set_mode("navigating")

        try:
            for i, wp in enumerate(waypoints):
                target_x = wp["x"]
                target_y = wp["y"]

                while True:
                    pose = self.odometry.get_pose()
                    result = self._compute_control(pose, target_x, target_y)

                    if result is None:
                        if self.on_event:
                            self.on_event("waypoint_reached", {"index": i, "x": target_x, "y": target_y})
                        break

                    vx, vy, omega = result
                    self.command_processor.set_command(vx, vy, omega)
                    await asyncio.sleep(config.COMMAND_INTERVAL)

            self.command_processor.stop()
            self.command_processor.set_mode("manual")
            if self.on_event:
                self.on_event("navigate_done", {})
        except asyncio.CancelledError:
            self.command_processor.stop()
            self.command_processor.set_mode("manual")

    def _compute_control(self, pose: dict, target_x: float, target_y: float):
        dx = target_x - pose["x"]
        dy = target_y - pose["y"]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < config.NAV_DEAD_ZONE:
            return None

        target_angle = math.atan2(dy, dx)
        angle_error = normalize_angle(target_angle - pose["theta"])

        speed = min(dist * config.NAV_KP_LINEAR, config.NAV_SPEED_LIMIT)
        vx = speed * math.cos(angle_error)
        vy = speed * math.sin(angle_error)
        omega = clamp(config.NAV_KP_ANGULAR * angle_error, -0.5, 0.5)

        return vx, vy, omega

    def start(self, waypoints: list) -> asyncio.Task:
        self.stop()
        self._task = asyncio.create_task(self.navigate(waypoints))
        return self._task

    def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()
        self.command_processor.stop()
        self.command_processor.set_mode("manual")
