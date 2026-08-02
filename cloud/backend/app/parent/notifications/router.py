"""Parent notification routes — settings (child-scoped) and center (parent-scoped)."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.notifications.schemas import (
    NotificationItem,
    NotificationSettingsOut,
    PaginatedNotifications,
    UpdateNotificationSettingsRequest,
)
from app.parent.notifications.service import (
    get_notification_settings,
    get_notifications,
    mark_notification_read,
    update_notification_settings,
)
from app.schemas.common import error, ok

# Child-scoped: notification settings
notification_settings_router = APIRouter(
    prefix="/children", tags=["parent-notification-settings"],
)


@notification_settings_router.get("/{child_id}/notification-settings")
async def get_settings(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_notification_settings(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(NotificationSettingsOut(**data).model_dump())


@notification_settings_router.put("/{child_id}/notification-settings")
async def update_settings(
    child_id: str,
    body: UpdateNotificationSettingsRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await update_notification_settings(
            db, parent_id, child_id, body.settings,
            body.dnd.enabled, body.dnd.start_time, body.dnd.end_time,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(NotificationSettingsOut(**data).model_dump())


# Parent-scoped: notification center
notification_center_router = APIRouter(
    prefix="/notifications", tags=["parent-notifications"],
)


@notification_center_router.get("")
async def list_notifications(
    filter_param: str = Query(default="all", alias="filter"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_notifications(db, parent_id, filter_param, page, page_size)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    return ok(PaginatedNotifications(
        items=[NotificationItem(**item) for item in data["items"]],
        unread_count=data["unread_count"],
        pagination=data["pagination"],
    ).model_dump())


@notification_center_router.put("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await mark_notification_read(db, parent_id, notification_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(
            status_code=404, content=error(404, "notification_not_found"),
        )
    return ok(data)
