"""Parent behavior routes — focus, posture, location, insights."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.behavior.schemas import (
    FocusOut,
    InsightsOut,
    LocationOut,
    PostureOut,
)
from app.parent.behavior.service import (
    get_focus,
    get_insights,
    get_location,
    get_posture,
)
from app.schemas.common import error, ok

behavior_router = APIRouter(prefix="/children", tags=["parent-behavior"])


@behavior_router.get("/{child_id}/behavior/focus")
async def focus(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_focus(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(FocusOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/posture")
async def posture(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_posture(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(PostureOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/location")
async def location(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_location(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(LocationOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/insights")
async def insights(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_insights(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(InsightsOut(**data).model_dump())
