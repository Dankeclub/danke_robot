"""Parent notifications business logic."""

import uuid
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationSettings
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))
DEFAULT_SETTINGS = {
    "task_completed": True, "task_expired": True,
    "child_replied": True, "behavior_alert": True,
    "realtime_alert": True, "goal_achieved": True,
    "daily_summary": True, "weekly_report": True,
    "device_offline": True, "learning_milestone": False,
}


async def get_notification_settings(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    result = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.child_id == child_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {
            "child_id": child_id, "settings": DEFAULT_SETTINGS,
            "dnd": {"enabled": False, "start_time": "22:00", "end_time": "08:00"},
            "updated_at": None,
        }
    return {
        "child_id": str(row.child_id),
        "settings": row.settings if isinstance(row.settings, dict) else DEFAULT_SETTINGS,
        "dnd": {
            "enabled": row.dnd_enabled,
            "start_time": row.dnd_start_time.isoformat() if row.dnd_start_time else "22:00",
            "end_time": row.dnd_end_time.isoformat() if row.dnd_end_time else "08:00",
        },
        "updated_at": row.updated_at,
    }


async def update_notification_settings(
    db: AsyncSession, parent_id: str, child_id: str,
    settings: dict, dnd_enabled: bool,
    dnd_start: str, dnd_end: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    st = time.fromisoformat(dnd_start) if dnd_start else None
    et = time.fromisoformat(dnd_end) if dnd_end else None

    stmt = pg_insert(NotificationSettings).values(
        child_id=child_id, settings=settings,
        dnd_enabled=dnd_enabled,
        dnd_start_time=st, dnd_end_time=et,
    ).on_conflict_do_update(
        index_elements=["child_id"],
        set_={
            "settings": settings,
            "dnd_enabled": dnd_enabled,
            "dnd_start_time": st,
            "dnd_end_time": et,
        },
    ).returning(NotificationSettings)
    result = await db.execute(stmt)
    row = result.scalar_one()
    await db.flush()
    return {
        "child_id": str(row.child_id),
        "settings": row.settings if isinstance(row.settings, dict) else DEFAULT_SETTINGS,
        "dnd": {
            "enabled": row.dnd_enabled,
            "start_time": row.dnd_start_time.isoformat() if row.dnd_start_time else "22:00",
            "end_time": row.dnd_end_time.isoformat() if row.dnd_end_time else "08:00",
        },
        "updated_at": row.updated_at,
    }


async def get_notifications(
    db: AsyncSession, parent_id: str,
    filter_type: str = "all", page: int = 1, page_size: int = 20,
) -> dict:
    query = select(Notification).where(Notification.parent_id == parent_id)
    if filter_type == "unread":
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc())

    unread_q = select(func.count()).select_from(
        select(Notification).where(
            Notification.parent_id == parent_id,
            Notification.is_read == False,
        ).subquery()
    )
    unread = (await db.execute(unread_q)).scalar() or 0

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    items = [
        {
            "notification_id": str(r.id), "type": r.notif_type, "icon": "",
            "title": r.title, "description": r.description,
            "child_id": str(r.child_id), "child_nickname": "",
            "is_read": r.is_read, "created_at": r.created_at,
        }
        for r in rows
    ]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "unread_count": unread, "items": items,
        "pagination": {
            "page": page, "page_size": page_size,
            "total": total, "total_pages": total_pages,
        },
    }


async def mark_notification_read(
    db: AsyncSession, parent_id: str, notification_id: str,
) -> dict | None:
    try:
        nid = uuid.UUID(notification_id)
    except ValueError:
        return None
    result = await db.execute(
        select(Notification).where(
            Notification.id == nid,
            Notification.parent_id == parent_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.is_read = True
    row.read_at = datetime.now(SHANGHAI_TZ)
    await db.flush()
    return {
        "notification_id": notification_id,
        "is_read": True, "read_at": row.read_at,
    }
