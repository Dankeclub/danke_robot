import time
import math


class Odometry:
    def __init__(self, max_speed_mps: float, max_omega_rps: float):
        self.max_speed_mps = max_speed_mps
        self.max_omega_rps = max_omega_rps
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_update = time.monotonic()

    def update(self, vx: float, vy: float, omega: float):
        now = time.monotonic()
        dt = now - self.last_update
        if dt <= 0:
            return
        self.last_update = now

        real_vx = vx * self.max_speed_mps
        real_vy = vy * self.max_speed_mps
        real_omega = omega * self.max_omega_rps

        half_theta = self.theta + real_omega * dt / 2
        self.x += (real_vx * math.cos(half_theta) - real_vy * math.sin(half_theta)) * dt
        self.y += (real_vx * math.sin(half_theta) + real_vy * math.cos(half_theta)) * dt
        self.theta += real_omega * dt

    def get_pose(self) -> dict:
        return {"x": self.x, "y": self.y, "theta": self.theta}

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_update = time.monotonic()

    def calibrate(self, x: float, y: float, theta: float):
        self.x = x
        self.y = y
        self.theta = theta
        self.last_update = time.monotonic()
