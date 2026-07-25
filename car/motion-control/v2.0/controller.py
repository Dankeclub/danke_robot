import asyncio
import logging
from LOBOROBOT import LOBOROBOT

log = logging.getLogger("controller")


class AsyncRobotController:
    def __init__(self):
        self.robot = LOBOROBOT()

    async def set_motors(self, m1: float, m2: float, m3: float, m4: float):
        await asyncio.to_thread(self._apply, m1, m2, m3, m4)

    def _apply(self, m1: float, m2: float, m3: float, m4: float):
        log.debug("apply motors: m1=%.2f m2=%.2f m3=%.2f m4=%.2f", m1, m2, m3, m4)
        motors = [
            (self.robot.motor1, m1),
            (self.robot.motor2, m2),
            (self.robot.motor3, m3),
            (self.robot.motor4, m4),
        ]
        for motor, val in motors:
            if abs(val) < 0.05:
                motor.stop()
            elif val > 0:
                motor.forward(min(abs(val), 1.0))
            else:
                motor.backward(min(abs(val), 1.0))

    async def stop(self):
        await asyncio.to_thread(self._stop_all)

    def _stop_all(self):
        self.robot.motor1.stop()
        self.robot.motor2.stop()
        self.robot.motor3.stop()
        self.robot.motor4.stop()
