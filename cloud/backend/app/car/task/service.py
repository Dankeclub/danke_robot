"""Car daily task business logic — ensure tasks, claim, list."""

import uuid
from datetime import UTC, date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.car.learning.schemas import difficulty_label as _diff_label
from app.car.learning.schemas import module_label as _mod_label
from app.models.config import LearningModuleConfig
from app.models.task import DailyTask


async def ensure_daily_tasks(
    db: AsyncSession, child_id: str, business_date: date
) -> list[DailyTask]:
    """Generate missing daily tasks for enabled modules, return all tasks."""
    child_uuid = uuid.UUID(child_id)

    # Fetch existing tasks for today
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.child_id == child_uuid,
            DailyTask.business_date == business_date,
            DailyTask.module.isnot(None),
        )
    )
    existing = {t.module: t for t in result.scalars().all()}

    # Fetch enabled module configs
    result = await db.execute(
        select(LearningModuleConfig).where(
            LearningModuleConfig.child_id == child_uuid,
            LearningModuleConfig.enabled == True,  # noqa: E712
        )
    )
    configs = {c.module: c for c in result.scalars().all()}

    SHANGHAI_TZ = timezone(timedelta(hours=8))

    # Create missing tasks
    # expires_at = 次日 00:00:00+08:00 per design spec
    now_shanghai = datetime.now(SHANGHAI_TZ)
    midnight = now_shanghai.replace(hour=0, minute=0, second=0, microsecond=0)
    expires_at = midnight + timedelta(days=1)

    for mod, cfg in configs.items():
        if mod in existing:
            continue

        title = f"今日{_mod_label(mod)}"
        task = DailyTask(
            child_id=child_uuid,
            business_date=business_date,
            module=mod,
            task_category="learning",
            title=title,
            status="assigned",
            config_snapshot={
                "difficulty": cfg.difficulty,
                "difficulty_label": _diff_label(mod, cfg.difficulty),
                "category": cfg.category,
                "batch_size": cfg.batch_size,
                "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
                "config_version": cfg.config_version,
            },
            progress_total=cfg.batch_size,
            expires_at=expires_at,
        )
        db.add(task)
        existing[mod] = task

    await db.flush()
    return list(existing.values())


async def get_tasks(
    db: AsyncSession, child_id: str, business_date: date | None = None
) -> list[dict]:
    """Get daily tasks for a child, optionally filtered by date."""
    bdate = business_date or date.today()

    tasks = await ensure_daily_tasks(db, child_id, bdate)
    return [_task_to_dict(t) for t in tasks]


async def claim_task(
    db: AsyncSession, child_id: str, task_id: str
) -> dict | None:
    """Claim a task (status: assigned -> claimed)."""
    task_uuid = uuid.UUID(task_id)

    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_uuid,
            DailyTask.child_id == uuid.UUID(child_id),
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    if task.status != "assigned":
        return _task_to_dict(task)

    task.status = "claimed"
    task.claimed_at = datetime.now(UTC)
    await db.flush()
    return _task_to_dict(task)


def _task_to_dict(t: DailyTask) -> dict:
    return {
        "task_id": str(t.id),
        "module": t.module,
        "module_label": _mod_label(t.module) if t.module else "",
        "task_category": t.task_category,
        "status": t.status,
        "title": t.title,
        "progress": {
            "completed_count": t.progress_completed,
            "total_count": t.progress_total,
            "accuracy": None,
            "is_final": t.status in ("completed", "expired"),
        },
        "expires_at": t.expires_at.isoformat() if t.expires_at else None,
        "claimed_at": t.claimed_at.isoformat() if t.claimed_at else None,
    }
