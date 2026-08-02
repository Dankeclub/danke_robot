"""Parent navigation routes — create remote instructions."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.navigation.schemas import NavigationOut, NavigationRequest
from app.parent.navigation.service import create_navigation
from app.schemas.common import error, ok

navigation_router = APIRouter(prefix="/children", tags=["parent-navigation"])


@navigation_router.post("/{child_id}/navigations")
async def create_navigation_endpoint(
    child_id: str,
    body: NavigationRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_navigation(
            db, parent_id, child_id,
            body.destination, body.route_key,
            body.module, body.custom_batch_size,
            body.title, body.expires_in_seconds,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if item is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(NavigationOut(**item).model_dump())
