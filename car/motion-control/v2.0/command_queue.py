import asyncio
import logging
import time

from controller import AsyncRobotController
from odometry import Odometry
import config

log = logging.getLogger("command_queue")


def mecanum_ik(vx: float, vy: float, omega: float) -> tuple:
    m1 = vx + vy + omega
    m2 = vx - vy - omega
    m3 = vx - vy + omega
    m4 = vx + vy - omega
    return proportional_normalize(m1, m2, m3, m4)


def proportional_normalize(m1: float, m2: float, m3: float, m4: float) -> tuple:
    max_val = max(abs(m1), abs(m2), abs(m3), abs(m4), 1.0)
    return (m1 / max_val, m2 / max_val, m3 / max_val, m4 / max_val)


class CommandProcessor:
    def __init__(self, controller: AsyncRobotController, odometry: Odometry):
        self.controller = controller
        self.odometry = odometry
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0
        self.last_command_time = time.monotonic()
        self.motor_values = (0.0, 0.0, 0.0, 0.0)
        self.mode = "idle"
        self._running = False

    def set_command(self, vx: float, vy: float, omega: float):
        self.vx = vx
        self.vy = vy
        self.omega = omega
        self.last_command_time = time.monotonic()
        log.debug("set_command: vx=%.2f vy=%.2f omega=%.2f", vx, vy, omega)

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def get_motor_values(self) -> tuple:
        return self.motor_values

    def get_mode(self) -> str:
        return self.mode

    def set_mode(self, mode: str):
        self.mode = mode

    async def run(self):
        self._running = True
        while self._running:
            now = time.monotonic()

            if now - self.last_command_time > config.DEADMAN_TIMEOUT:
                vx, vy, omega = 0.0, 0.0, 0.0
            else:
                vx, vy, omega = self.vx, self.vy, self.omega

            m1, m2, m3, m4 = mecanum_ik(vx, vy, omega)
            self.motor_values = (m1, m2, m3, m4)

            if abs(vx) > 0.01 or abs(vy) > 0.01 or abs(omega) > 0.01:
                log.debug("motors: m1=%.2f m2=%.2f m3=%.2f m4=%.2f", m1, m2, m3, m4)

            await self.controller.set_motors(m1, m2, m3, m4)
            self.odometry.update(vx, vy, omega)

            await asyncio.sleep(config.COMMAND_INTERVAL)

    def shutdown(self):
        self._running = False
