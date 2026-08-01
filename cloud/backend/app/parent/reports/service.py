"""Parent reports business logic — progress, sessions, wrong-answers, weekly."""

import uuid
from datetime import date, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord, WrongAnswer
from app.models.learning import LearningSession
from app.models.task import DailyTask
from app.parent.service import datetime_range_shanghai, verify_parent_access

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}
SHANGHAI_TZ = timezone(timedelta(hours=8))


# --- Learning Progress ---

async def get_learning_progress(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict | None:
    """Aggregate learning progress per module and overall."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    # Aggregate tasks per module
    task_result = await db.execute(
        select(
            DailyTask.module,
            func.count().label("total"),
            func.count().filter(DailyTask.status == "completed").label("completed"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(start_date, end_date),
        )
        .group_by(DailyTask.module)
    )
    task_rows = task_result.all()

    # Aggregate answers per module for accuracy
    start_dt, _ = datetime_range_shanghai(start_date)
    _, end_dt_end = datetime_range_shanghai(end_date)
    end_dt = end_dt_end  # inclusive end

    answer_result = await db.execute(
        select(
            AnswerRecord.module,
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct).label("correct"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            AnswerRecord.answered_at >= start_dt,
            AnswerRecord.answered_at < end_dt + timedelta(days=1),
        )
        .group_by(AnswerRecord.module)
    )
    answer_rows = {r.module: (r.total, r.correct) for r in answer_result.all()}

    modules = []
    overall_completed = 0
    overall_total = 0
    overall_correct = 0
    overall_wrong = 0

    for mod, total, completed in task_rows:
        ans_total, ans_correct = answer_rows.get(mod, (0, 0))
        accuracy = round(ans_correct / ans_total, 4) if ans_total > 0 else None
        modules.append({
            "module": mod,
            "module_label": MODULE_LABELS.get(mod, mod),
            "completed_tasks": completed or 0,
            "total_tasks": total or 0,
            "accuracy": accuracy,
            "total_correct": ans_correct,
            "total_wrong": ans_total - ans_correct,
        })
        overall_completed += completed or 0
        overall_total += total or 0
        overall_correct += ans_correct
        overall_wrong += ans_total - ans_correct

    overall_ans_total = overall_correct + overall_wrong
    overall_accuracy = (
        round(overall_correct / overall_ans_total, 4)
        if overall_ans_total > 0 else None
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "modules": modules,
        "overall_completed": overall_completed,
        "overall_total": overall_total,
        "overall_accuracy": overall_accuracy,
        "overall_correct": overall_correct,
        "overall_wrong": overall_wrong,
    }


# --- Learning Sessions ---

async def get_sessions(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    module: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    """Paginated list of learning sessions with answer summaries."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    # Build query
    query = (
        select(LearningSession)
        .where(LearningSession.child_id == child_id)
    )

    if module:
        query = query.where(LearningSession.module == module)
    if status:
        query = query.where(LearningSession.status == status)
    if start_date:
        s_dt, _ = datetime_range_shanghai(start_date)
        query = query.where(LearningSession.created_at >= s_dt)
    if end_date:
        _, e_dt = datetime_range_shanghai(end_date)
        query = query.where(LearningSession.created_at < e_dt)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(LearningSession.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        summary = await _get_session_summary(db, s.id)
        items.append({
            "session_id": str(s.id),
            "module": s.module,
            "module_label": MODULE_LABELS.get(s.module, s.module),
            "source": s.source,
            "status": s.status,
            "created_at": s.created_at,
            "completed_at": s.updated_at if s.status == "completed" else None,
            "summary": summary,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


async def get_session_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    session_id: str,
) -> dict | None:
    """Get a single learning session with answer summary."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return None

    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == sid_uuid,
            LearningSession.child_id == child_id,
        )
    )
    s = result.scalar_one_or_none()
    if s is None:
        return None

    summary = await _get_session_summary(db, s.id)

    return {
        "session_id": str(s.id),
        "module": s.module,
        "module_label": MODULE_LABELS.get(s.module, s.module),
        "source": s.source,
        "status": s.status,
        "created_at": s.created_at,
        "completed_at": s.updated_at if s.status == "completed" else None,
        "summary": summary,
    }


async def _get_session_summary(db: AsyncSession, session_id: uuid.UUID) -> dict:
    """Aggregate answer records for a session into a summary."""
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct).label("correct"),
        )
        .where(AnswerRecord.session_id == session_id)
    )
    row = result.one()
    total = row.total or 0
    correct = row.correct or 0
    wrong = total - correct
    accuracy = round(correct / total, 4) if total > 0 else None

    return {
        "completed_count": correct,
        "total_count": total,
        "accuracy": accuracy,
        "correct_count": correct,
        "wrong_count": wrong,
        "total_active_duration_ms": 0,
    }


# --- Wrong Answers ---

async def get_wrong_answers(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    module: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    """Paginated list of wrong answers."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    query = (
        select(WrongAnswer)
        .where(WrongAnswer.child_id == child_id)
    )
    if module:
        query = query.where(WrongAnswer.module == module)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(WrongAnswer.last_wrong_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.scalars().all()

    items = []
    for r in rows:
        qs = r.question_snapshot if isinstance(r.question_snapshot, dict) else {}
        items.append({
            "wrong_answer_id": str(r.id),
            "module": r.module,
            "module_label": MODULE_LABELS.get(r.module, r.module),
            "question_snapshot": qs if qs else None,
            "selected_option_id": r.selected_option_id,
            "first_wrong_at": r.first_wrong_at,
            "last_wrong_at": r.last_wrong_at,
            "wrong_count": r.wrong_count,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


# --- Weekly Report ---

def _week_boundaries(week_key: str) -> tuple[date, date]:
    """Parse a week_key (Monday's date) and return (monday, sunday)."""
    monday = date.fromisoformat(week_key)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _recent_week_keys(count: int = 8) -> list[dict]:
    """Return the last `count` week keys ending at the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    keys = []
    for i in range(count):
        wk = monday - timedelta(weeks=i)
        keys.append({
            "week_key": wk.isoformat(),
            "label": f"{wk} ~ {wk + timedelta(days=6)}",
            "start_date": wk,
            "end_date": wk + timedelta(days=6),
        })
    return keys


async def get_weekly_report_list(
    db: AsyncSession, parent_id: str, child_id: str,
) -> list[dict] | None:
    """Return last 8 week keys without detailed data."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    return _recent_week_keys(8)


async def get_weekly_report_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    week_key: str,
) -> dict | None:
    """Build a weekly report for the given week_key (Monday's date)."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        monday, sunday = _week_boundaries(week_key)
    except ValueError:
        return None

    return await _build_weekly_report(db, child_id, week_key, monday, sunday)


async def _build_weekly_report(
    db: AsyncSession, child_id: str, week_key: str, monday: date, sunday: date,
) -> dict:
    """Aggregate learning data for a week and return a WeeklyReport dict."""

    # Tasks completed in this week
    task_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(DailyTask.status == "completed").label("completed"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(monday, sunday),
        )
    )
    task_row = task_result.one()

    # Modules touched
    mod_result = await db.execute(
        select(DailyTask.module)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(monday, sunday),
        )
        .distinct()
    )
    modules_touched = [r[0] for r in mod_result.all()]

    # Answers accuracy this week
    monday_dt, _ = datetime_range_shanghai(monday)
    _, sunday_dt = datetime_range_shanghai(sunday)
    answer_end = sunday_dt + timedelta(days=1)

    ans_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct).label("correct"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            AnswerRecord.answered_at >= monday_dt,
            AnswerRecord.answered_at < answer_end,
        )
    )
    ans_row = ans_result.one()
    ans_total = ans_row.total or 0
    ans_correct = ans_row.correct or 0
    avg_accuracy = round(ans_correct / ans_total, 4) if ans_total > 0 else None

    label = f"{monday} ~ {sunday}"

    return {
        "week_key": week_key,
        "label": label,
        "start_date": monday,
        "end_date": sunday,
        "learning_summary": {
            "total_active_duration_minutes": 0,
            "completed_tasks": task_row.completed or 0,
            "total_tasks": task_row.total or 0,
            "average_accuracy": avg_accuracy,
            "modules_touched": modules_touched,
        },
        "behavior_summary": {
            "focus_score": 0, "focus_change_percent": 0,
            "posture_score": 0, "posture_change_percent": 0,
            "anomaly_count": 0, "discovery_count": 0,
        },
        "focus_daily_series": [],
        "posture_weekly_series": [],
        "anomalies": [],
        "discoveries": [],
        "ai_summary": "",
    }
