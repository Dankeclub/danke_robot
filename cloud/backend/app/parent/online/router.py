"""Parent online status route."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.online.schemas import OnlineStatusOut
from app.parent.online.service import get_online_status
from app.schemas.common import error, ok

online_router = APIRouter(prefix="/children", tags=["parent-online"])


@online_router.get("/{child_id}/online-status")
async def online_status(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_online_status(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(OnlineStatusOut(**data).model_dump())
