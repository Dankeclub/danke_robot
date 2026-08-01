"""Car daily task routes — list, detail, claim."""

from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.car.task.service import claim_task, get_tasks
from app.db import get_db
from app.schemas.common import error, ok

task_router = APIRouter(prefix="/today-tasks", tags=["car-task"])


@task_router.get("")
async def list_tasks(
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """List today's tasks for the current child."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        tasks = await get_tasks(db, child_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok({"business_date": str(date.today()), "timezone": "Asia/Shanghai", "items": tasks})


@task_router.get("/{task_id}")
async def get_task_detail(
    task_id: str,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task's details."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    from app.models.task import DailyTask

    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_id,
            DailyTask.child_id == child_id,
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        return JSONResponse(status_code=404, content=error(404, "task_not_found"))

    from app.car.task.service import _task_to_dict

    return ok(_task_to_dict(task))


@task_router.post("/{task_id}/claim")
async def do_claim_task(
    task_id: str,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Claim a task — move from assigned to claimed."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        result = await claim_task(db, child_id, task_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if result is None:
        return JSONResponse(status_code=404, content=error(404, "task_not_found"))

    return ok(result)
