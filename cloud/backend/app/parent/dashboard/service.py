"""Parent dashboard business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord
from app.models.learning import LearningSession
from app.models.parent_child import ParentChild
from app.models.task import DailyTask
from app.parent.service import datetime_range_shanghai, today_shanghai

MODULE_LABELS = {
    "science": "科学探秘",
    "math": "数学思维",
    "english": "英语角",
    "poems": "诗词歌赋",
    "music": "音乐乐园",
    "quiz": "趣味问答",
}




async def get_dashboard_today(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    """Build today's dashboard for a child.

    Returns aggregated stats across all tasks, answers, and sessions
    for the current business date.
    """
    # Verify access
    result = await db.execute(
        select(ParentChild).where(
            ParentChild.parent_id == parent_id,
            ParentChild.child_id == child_id,
            ParentChild.status == "active",
        )
    )
    if result.scalar_one_or_none() is None:
        return None

    today = today_shanghai()

    # Get today's tasks
    task_result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date == today,
        )
        .order_by(DailyTask.created_at.desc())
    )
    tasks = task_result.scalars().all()

    # Get today's learning sessions
    today_start, tomorrow_start = datetime_range_shanghai(today)

    session_result = await db.execute(
        select(LearningSession)
        .where(
            LearningSession.child_id == child_id,
            LearningSession.created_at >= today_start,
            LearningSession.created_at < tomorrow_start,
        )
    )
    sessions = session_result.scalars().all()

    # Get today's answer records for accuracy
    answer_result = await db.execute(
        select(AnswerRecord)
        .where(
            AnswerRecord.child_id == child_id,
            AnswerRecord.answered_at >= today_start,
            AnswerRecord.answered_at < tomorrow_start,
        )
    )
    answers = answer_result.scalars().all()

    # Calculate stats
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    active_sessions = sum(1 for s in sessions if s.status == "active")

    total_correct = sum(1 for a in answers if a.is_correct)
    total_wrong = sum(1 for a in answers if not a.is_correct)
    total_answers = len(answers)
    overall_accuracy = (
        round(total_correct / total_answers, 4) if total_answers > 0 else None
    )

    # Build task list
    task_list = []
    for t in tasks:
        task_list.append({
            "task_id": str(t.id),
            "task_category": t.task_category,
            "module": t.module,
            "module_label": MODULE_LABELS.get(t.module, t.module) if t.module else None,
            "status": t.status,
            "title": t.title,
            "progress": {
                "completed_count": t.progress_completed,
                "total_count": t.progress_total,
                "accuracy": None,
                "correct_count": None,
                "wrong_count": None,
                "is_final": t.status == "completed",
            },
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
        })

    # Build per-module progress
    module_map: dict[str, dict] = {}
    for t in tasks:
        mod = t.module
        if mod not in module_map:
            module_map[mod] = {
                "module": mod,
                "module_label": MODULE_LABELS.get(mod, mod),
                "completed_tasks": 0,
                "total_tasks": 0,
                "accuracy": None,
                "active_sessions": 0,
            }
        module_map[mod]["total_tasks"] += 1
        if t.status == "completed":
            module_map[mod]["completed_tasks"] += 1

    for s in sessions:
        mod = s.module
        if s.status == "active" and mod in module_map:
            module_map[mod]["active_sessions"] += 1

    modules = list(module_map.values())

    return {
        "date": today.isoformat(),
        "total_tasks": len(tasks),
        "completed_tasks": completed_tasks,
        "overall_accuracy": overall_accuracy,
        "total_correct": total_correct,
        "total_wrong": total_wrong,
        "active_sessions": active_sessions,
        "total_learning_minutes": 0,  # Phase 2: not yet tracked
        "tasks": task_list,
        "modules": modules,
    }
