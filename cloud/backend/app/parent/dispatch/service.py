"""Parent dispatch business logic — today-tasks view + dispatched tasks."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import DailyTask
from app.parent.dispatch.schemas import MODULE_LABELS
from app.parent.service import (
    datetime_range_shanghai,
    today_shanghai,
    verify_parent_access,
)


async def get_today_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    business_date: date | None = None,
) -> list[dict] | None:
    """Get today's learning tasks (module IS NOT NULL) for a child.

    Returns None if parent has no access to child.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    bdate = business_date or today_shanghai()

    result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date == bdate,
            DailyTask.module.isnot(None),
        )
        .order_by(DailyTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


async def get_task_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    task_id: str,
) -> dict | None:
    """Get a single task detail by ID. Only returns learning tasks."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return None

    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_uuid,
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    return _task_to_dict(task)


async def get_dispatched_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    business_date: date | None = None,
) -> list[dict] | None:
    """Get dispatched (non-learning) tasks for a child."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    bdate = business_date or today_shanghai()

    result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date == bdate,
            DailyTask.task_category.in_(["lifestyle", "sports", "custom"]),
        )
        .order_by(DailyTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


async def create_dispatched_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    tasks: list[dict],
) -> list[dict] | None:
    """Create dispatched (non-learning) tasks for a child.

    Each task dict: {task_category, title, module?}
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    today = today_shanghai()
    today_start, _ = datetime_range_shanghai(today)
    expires_at = today_start.replace(hour=23, minute=59, second=59)

    created = []
    for t in tasks:
        module = None  # only non-learning tasks here; learning handled by today-tasks
        task = DailyTask(
            child_id=child_id,
            business_date=today,
            module=module,
            task_category=t.get("task_category", "custom"),
            title=t["title"],
            status="assigned",
            progress_total=1,
            expires_at=expires_at,
        )
        db.add(task)
        created.append(task)

    await db.flush()
    return [_task_to_dict(t) for t in created]


def _task_to_dict(t: DailyTask) -> dict:
    return {
        "task_id": str(t.id),
        "task_category": t.task_category,
        "module": t.module,
        "module_label": MODULE_LABELS.get(t.module, "") if t.module else None,
        "status": t.status,
        "title": t.title,
        "progress": {
            "completed_count": t.progress_completed,
            "total_count": t.progress_total,
            "accuracy": None,
            "correct_count": None,
            "wrong_count": None,
            "is_final": t.status in ("completed", "expired"),
        },
        "expires_at": t.expires_at.isoformat() if t.expires_at else None,
    }
