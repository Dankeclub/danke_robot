"""Parent children routes — list, create, get, update, delete children."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.children.schemas import (
    ChildDetail,
    ChildSummary,
    CreateChildRequest,
    UpdateChildRequest,
)
from app.parent.children.service import (
    create_child,
    get_child_detail,
    list_children,
    unbind_child,
    update_child,
)
from app.schemas.common import error, ok

children_router = APIRouter(prefix="/children", tags=["parent-children"])


@children_router.get("")
async def get_children(
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get list of children for the current parent."""
    try:
        items = await list_children(db, parent_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok([ChildSummary(**item).model_dump() for item in items])


@children_router.post("")
async def create_child_endpoint(
    body: CreateChildRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Create a new child and bind to the current parent."""
    try:
        child = await create_child(
            db,
            parent_id=parent_id,
            nickname=body.nickname,
            family_id=body.family_id,
            avatar_url=body.avatar_url,
            birth_date=body.birth_date.isoformat() if body.birth_date else None,
            gender=body.gender,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg.startswith("invalid_gender"):
            return JSONResponse(status_code=400, content=error(400, msg))
        if msg == "family_not_found":
            return JSONResponse(status_code=404, content=error(404, msg))
        return JSONResponse(status_code=400, content=error(400, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(ChildSummary(**child).model_dump())


@children_router.get("/{child_id}")
async def get_child(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get child detail."""
    try:
        child = await get_child_detail(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if child is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(ChildDetail(**child).model_dump())


@children_router.put("/{child_id}")
async def update_child_endpoint(
    child_id: str,
    body: UpdateChildRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Update child profile."""
    try:
        updated = await update_child(
            db,
            parent_id=parent_id,
            child_id=child_id,
            nickname=body.nickname,
            avatar_url=body.avatar_url,
            birth_date=body.birth_date.isoformat() if body.birth_date else None,
            gender=body.gender,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        return JSONResponse(status_code=400, content=error(400, str(e)))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if updated is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(ChildSummary(**updated).model_dump())


@children_router.delete("/{child_id}")
async def delete_child(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Unbind a child from the parent (soft delete)."""
    try:
        found = await unbind_child(db, parent_id, child_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if not found:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok()
