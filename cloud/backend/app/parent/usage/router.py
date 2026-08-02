"""Parent usage routes — series, module breakdown."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.usage.schemas import ModuleBreakdownOut, UsageSeriesOut
from app.parent.usage.service import get_module_breakdown, get_usage_series
from app.schemas.common import error, ok

usage_router = APIRouter(prefix="/children", tags=["parent-usage"])


@usage_router.get("/{child_id}/usage")
async def usage_series(
    child_id: str,
    granularity: str = Query(default="day", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_usage_series(db, parent_id, child_id, granularity)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(UsageSeriesOut(**data).model_dump())


@usage_router.get("/{child_id}/usage/modules")
async def module_breakdown(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_module_breakdown(db, parent_id, child_id, date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(ModuleBreakdownOut(**data).model_dump())
