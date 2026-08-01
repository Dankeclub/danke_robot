"""Car learning routes — park, sessions, batches."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.car.learning.schemas import LearningParkOut, ModuleConfigOut, SessionRequest
from app.car.learning.service import create_batch, create_session, get_learning_park
from app.db import get_db
from app.schemas.common import error, ok

learning_router = APIRouter(prefix="/learning", tags=["car-learning"])


@learning_router.get("/park")
async def learning_park(
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Return 6 learning module states with configs and active sessions."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        modules = await get_learning_park(db, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(LearningParkOut(modules=[ModuleConfigOut(**m) for m in modules]).model_dump())


@learning_router.post("/{module}/sessions")
async def create_learning_session(
    module: str,
    body: SessionRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Create or resume a learning session for a module."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    valid_modules = {"science", "math", "english", "poems", "music", "quiz"}
    if module not in valid_modules:
        return JSONResponse(status_code=404, content=error(404, "module_not_found"))

    try:
        session = await create_session(
            db, child_id, module, body.source, body.task_id, body.navigation_id,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(session)


@learning_router.post("/{module}/sessions/{session_id}/batches")
async def create_learning_batch(
    module: str,
    session_id: str,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Create or return the next batch of content for a session."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        batch = await create_batch(db, child_id, module, session_id)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg == "session_not_found":
            return JSONResponse(status_code=404, content=error(404, msg))
        if msg == "content_pool_exhausted":
            return JSONResponse(status_code=409, content=error(409, msg))
        return JSONResponse(status_code=500, content=error(500, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(batch)
