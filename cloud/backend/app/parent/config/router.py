"""Parent learning config routes — get/update config and audit history."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.config.schemas import (
    ConfigAuditEntry,
    ConfigAuditList,
    LearningConfigModule,
    UpdateLearningConfigRequest,
)
from app.parent.config.service import (
    get_config_audit,
    get_learning_config,
    update_learning_config,
)
from app.schemas.common import error, ok

config_router = APIRouter(prefix="/children", tags=["parent-config"])


@config_router.get("/{child_id}/learning/config")
async def get_config(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get current learning config for all modules."""
    try:
        modules = await get_learning_config(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if modules is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([LearningConfigModule(**m).model_dump() for m in modules])


@config_router.put("/{child_id}/learning/config")
async def update_config(
    child_id: str,
    body: UpdateLearningConfigRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Bulk update learning module configs."""
    mod_list = []
    for m in body.modules:
        mod_list.append({
            "module": m.module,
            "enabled": m.enabled,
            "difficulty": m.difficulty,
            "category": m.category,
            "batch_size": m.batch_size,
            "min_repeat_interval_seconds": m.min_repeat_interval_seconds,
        })

    try:
        updated = await update_learning_config(db, parent_id, child_id, mod_list)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg.startswith("module_not_found"):
            return JSONResponse(status_code=400, content=error(400, msg))
        return JSONResponse(status_code=400, content=error(400, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if updated is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([LearningConfigModule(**m).model_dump() for m in updated])


@config_router.get("/{child_id}/learning/config/audit")
async def get_config_audit_endpoint(
    child_id: str,
    module: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get config change audit history."""
    try:
        result = await get_config_audit(
            db, parent_id, child_id, module=module, limit=limit, cursor=cursor,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if result is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(ConfigAuditList(
        items=[ConfigAuditEntry(**item) for item in result["items"]],
        has_more=result["has_more"],
        next_cursor=result["next_cursor"],
    ).model_dump())
