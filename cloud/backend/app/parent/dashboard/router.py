"""Parent dashboard routes — today's learning overview."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.dashboard.schemas import DashboardTodayOut
from app.parent.dashboard.service import get_dashboard_today
from app.schemas.common import error, ok

dashboard_router = APIRouter(prefix="/children", tags=["parent-dashboard"])


@dashboard_router.get("/{child_id}/dashboard/today")
async def dashboard_today(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get today's learning dashboard for a child."""
    try:
        data = await get_dashboard_today(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(DashboardTodayOut(**data).model_dump())
