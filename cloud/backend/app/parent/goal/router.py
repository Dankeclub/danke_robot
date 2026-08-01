"""Parent learning goal routes — GET/PUT daily learning goal."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.goal.schemas import LearningGoalOut, UpdateLearningGoalRequest
from app.parent.goal.service import get_learning_goal, upsert_learning_goal
from app.schemas.common import error, ok

goal_router = APIRouter(prefix="/children", tags=["parent-goal"])


@goal_router.get("/{child_id}/learning/goal")
async def get_goal(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get daily learning goal for a child."""
    try:
        data = await get_learning_goal(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningGoalOut(**data).model_dump())


@goal_router.put("/{child_id}/learning/goal")
async def update_goal(
    child_id: str,
    body: UpdateLearningGoalRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Update daily learning goal for a child."""
    modules_data = [
        {"module": m.module, "goal_minutes": m.goal_minutes}
        for m in body.modules
    ]

    try:
        data = await upsert_learning_goal(
            db, parent_id, child_id, body.daily_goal_minutes, modules_data,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg.startswith("invalid_module"):
            return JSONResponse(status_code=400, content=error(400, msg))
        return JSONResponse(status_code=400, content=error(400, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningGoalOut(**data).model_dump())
