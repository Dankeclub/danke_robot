"""Parent usage business logic — series and module breakdown."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord
from app.models.learning import LearningSession
from app.models.task import DailyTask
from app.parent.service import verify_parent_access

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}


async def get_usage_series(
    db: AsyncSession, parent_id: str, child_id: str,
    granularity: str = "day",
) -> dict | None:
    """Return daily/weekly/monthly usage minutes series.

    Phase 3 approximation: 5 min per completed task + 5 min per session.
    Phase 4: use actual behavior_event duration data.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    days = {"day": 7, "week": 28, "month": 90}.get(granularity, 7)
    cutoff = date.today() - timedelta(days=days - 1)
    today = date.today()

    task_result = await db.execute(
        select(
            DailyTask.business_date,
            func.count().label("cnt"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date >= cutoff,
            DailyTask.status == "completed",
        )
        .group_by(DailyTask.business_date)
    )
    task_map = {str(r.business_date): r.cnt for r in task_result.all()}

    sess_result = await db.execute(
        select(
            func.date(LearningSession.created_at).label("d"),
            func.count().label("cnt"),
        )
        .where(
            LearningSession.child_id == child_id,
            func.date(LearningSession.created_at) >= cutoff,
        )
        .group_by(func.date(LearningSession.created_at))
    )
    sess_map = {str(r.d): r.cnt for r in sess_result.all()}

    series = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        d_str = d.isoformat()
        tasks = task_map.get(d_str, 0)
        sessions_val = sess_map.get(d_str, 0)
        minutes = tasks * 5 + sessions_val * 5
        series.append({"date": d, "total_minutes": minutes})

    return {
        "granularity": granularity, "daily_goal_minutes": 30, "series": series,
    }


async def get_module_breakdown(
    db: AsyncSession, parent_id: str, child_id: str,
    target_date: date | None = None,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    if target_date is None:
        target_date = date.today()

    result = await db.execute(
        select(
            AnswerRecord.module,
            func.count().label("cnt"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            func.date(AnswerRecord.answered_at) == target_date,
        )
        .group_by(AnswerRecord.module)
    )
    rows = result.all()
    total = sum(r.cnt for r in rows)
    modules = []
    for module, cnt in rows:
        pct = round(cnt / total * 100) if total > 0 else 0
        modules.append({
            "module": module,
            "module_label": MODULE_LABELS.get(module, module),
            "minutes": cnt * 2,
            "percent": pct,
        })
    return {
        "date": target_date,
        "total_minutes": total * 2,
        "modules": modules,
    }
