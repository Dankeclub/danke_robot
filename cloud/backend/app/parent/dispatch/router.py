"""Parent dispatch routes — today tasks list/detail, dispatched tasks."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.dispatch.schemas import (
    DispatchTasksRequest,
    TodayTaskOut,
)
from app.parent.dispatch.service import (
    create_dispatched_tasks,
    get_dispatched_tasks,
    get_task_detail,
    get_today_tasks,
)
from app.schemas.common import error, ok

dispatch_router = APIRouter(prefix="/children", tags=["parent-dispatch"])


@dispatch_router.get("/{child_id}/today-tasks")
async def list_today_tasks(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get today's learning tasks for a child."""
    try:
        items = await get_today_tasks(db, parent_id, child_id, business_date=date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])


@dispatch_router.get("/{child_id}/today-tasks/{task_id}")
async def get_today_task_detail(
    child_id: str,
    task_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task detail."""
    try:
        item = await get_task_detail(db, parent_id, child_id, task_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if item is None:
        return JSONResponse(status_code=404, content=error(404, "task_not_found"))

    return ok(TodayTaskOut(**item).model_dump())


@dispatch_router.get("/{child_id}/dispatched-tasks")
async def list_dispatched_tasks(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatched (non-learning) tasks for a child."""
    try:
        items = await get_dispatched_tasks(db, parent_id, child_id, business_date=date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])


@dispatch_router.post("/{child_id}/dispatched-tasks")
async def create_dispatched_tasks_endpoint(
    child_id: str,
    body: DispatchTasksRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Create dispatched tasks for a child."""
    # Dispatched tasks are non-learning only; learning tasks go through today-tasks
    for t in body.tasks:
        if t.task_category == "learning":
            return JSONResponse(
                status_code=400,
                content=error(400, "learning_tasks_not_allowed_here"),
            )

    tasks_data = [
        {"task_category": t.task_category, "module": t.module, "title": t.title}
        for t in body.tasks
    ]

    try:
        items = await create_dispatched_tasks(db, parent_id, child_id, tasks_data)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        return JSONResponse(status_code=400, content=error(400, str(e)))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])
