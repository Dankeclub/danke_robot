"""Parent learning goal business logic."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import LearningGoal
from app.parent.goal.schemas import MODULE_LABELS, VALID_MODULES
from app.parent.service import verify_parent_access


async def get_learning_goal(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    """Get learning goal for a child. Returns defaults if not set."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    result = await db.execute(
        select(LearningGoal).where(LearningGoal.child_id == child_id)
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        return _default_goal()

    return _goal_to_dict(goal)


async def upsert_learning_goal(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    daily_goal_minutes: int,
    modules: list[dict],
) -> dict | None:
    """Create or update learning goal for a child.

    Raises ValueError if any module name is invalid.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    # Validate modules
    for m in modules:
        mod_name = m.get("module", "")
        if mod_name not in VALID_MODULES:
            raise ValueError(f"invalid_module: {mod_name}")

    # Validate per-module sum ≤ daily total
    module_sum = sum(m.get("goal_minutes", 0) for m in modules)
    if module_sum > daily_goal_minutes:
        raise ValueError(
            f"goal_module_sum_exceeds_total: {module_sum} > {daily_goal_minutes}"
        )

    module_goals = [
        {"module": m["module"], "goal_minutes": m.get("goal_minutes", 0)}
        for m in modules
    ]

    stmt = pg_insert(LearningGoal).values(
        child_id=child_id,
        daily_goal_minutes=daily_goal_minutes,
        module_goals=module_goals,
    ).on_conflict_do_update(
        index_elements=["child_id"],
        set_={
            "daily_goal_minutes": daily_goal_minutes,
            "module_goals": module_goals,
        },
    ).returning(LearningGoal)

    result = await db.execute(stmt)
    goal = result.scalar_one()
    await db.flush()

    return _goal_to_dict(goal)


def _goal_to_dict(goal: LearningGoal) -> dict:
    """Convert a LearningGoal ORM object to response dict."""
    raw_modules = goal.module_goals if isinstance(goal.module_goals, list) else []
    modules = []
    for m in raw_modules:
        mod_name = m.get("module", "")
        modules.append({
            "module": mod_name,
            "module_label": MODULE_LABELS.get(mod_name, mod_name),
            "goal_minutes": m.get("goal_minutes", 0),
        })
    return {
        "daily_goal_minutes": goal.daily_goal_minutes,
        "modules": modules,
    }


def _default_goal() -> dict:
    """Return default goal (30 min total, empty per-module)."""
    return {
        "daily_goal_minutes": 30,
        "modules": [],
    }
