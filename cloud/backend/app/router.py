"""Top-level router aggregation."""

from fastapi import APIRouter

from app.auth.router_car import car_auth_router
from app.auth.router_parent import parent_auth_router
from app.car.learning.router import learning_router
from app.car.task.router import task_router
from app.car.files.router import files_router as car_files_router
from app.car.messages.router import messages_router as car_messages_router
from app.parent.behavior.router import behavior_router
from app.parent.children.router import children_router
from app.parent.config.router import config_router
from app.parent.dashboard.router import dashboard_router
from app.parent.device.router import device_router
from app.parent.dispatch.router import dispatch_router
from app.parent.files.router import files_router
from app.parent.goal.router import goal_router
from app.parent.messages.router import messages_router
from app.parent.navigation.router import navigation_router
from app.parent.notifications.router import (
    notification_center_router,
    notification_settings_router,
)
from app.parent.online.router import online_router
from app.parent.reports.router import reports_router
from app.parent.usage.router import usage_router
from app.telemetry.router import telemetry_router

top_router = APIRouter()


@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}


# Car device API
car_router = APIRouter(prefix="/v1/api/car")
car_router.include_router(car_auth_router)
car_router.include_router(learning_router)
car_router.include_router(task_router)
car_router.include_router(telemetry_router)
car_router.include_router(car_files_router)
car_router.include_router(car_messages_router)
top_router.include_router(car_router)

# Parent mini-program API
parent_router = APIRouter(prefix="/v1/api/parent")
parent_router.include_router(parent_auth_router)
parent_router.include_router(children_router)
parent_router.include_router(device_router)
parent_router.include_router(config_router)
parent_router.include_router(dashboard_router)
parent_router.include_router(goal_router)
parent_router.include_router(dispatch_router)
parent_router.include_router(reports_router)
parent_router.include_router(behavior_router)
parent_router.include_router(usage_router)
parent_router.include_router(online_router)
parent_router.include_router(messages_router)
parent_router.include_router(navigation_router)
parent_router.include_router(notification_settings_router)
parent_router.include_router(notification_center_router)
parent_router.include_router(files_router)
top_router.include_router(parent_router)
