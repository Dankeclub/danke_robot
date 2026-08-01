"""Telemetry event ingestion routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.db import get_db
from app.schemas.common import error, ok
from app.telemetry.schemas import BatchEventsRequest
from app.telemetry.service import (
    complete_session,
    get_session_summary,
    insert_events,
    process_answer_events,
)

telemetry_router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@telemetry_router.post("/events:batch")
async def batch_events(
    body: BatchEventsRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a batch of telemetry events from a car device.

    Idempotent: duplicate event_id values are silently accepted but not
    duplicated in storage.
    """
    device_id = device["device_id"]
    child_id = device["child_id"]

    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    events_data = [
        {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "module": e.module,
            "timestamp": e.timestamp,
            "payload": e.payload,
        }
        for e in body.events
    ]

    accepted, duplicates = await insert_events(
        db, device_id, child_id, events_data
    )

    # Process answer events (judge correctness, track wrong answers)
    await process_answer_events(
        db, child_id,
        [
            {
                "event_type": e.event_type,
                "session_id": e.payload.get("session_id"),
                "batch_id": e.payload.get("batch_id"),
                "question_id": e.payload.get("question_id"),
                "selected_option_id": e.payload.get("selected_option_id"),
                "module": e.module,
                "timestamp": e.timestamp,
                "answer_duration_ms": e.payload.get("answer_duration_ms"),
            }
            for e in body.events
        ],
    )

    await db.commit()

    return ok({"accepted": accepted, "duplicates": duplicates})


@telemetry_router.post("/sessions/{session_id}/complete")
async def complete_learning_session(
    session_id: str,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Request completion check for a learning session."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        result = await complete_session(db, child_id, session_id)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        if str(e) == "session_not_found":
            return JSONResponse(status_code=404, content=error(404, "session_not_found"))
        return JSONResponse(status_code=500, content=error(500, str(e)))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(result)


@telemetry_router.get("/sessions/{session_id}/summary")
async def session_summary(
    session_id: str,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Get current summary stats for a learning session."""
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        result = await get_session_summary(db, child_id, session_id)
    except ValueError as e:
        if str(e) == "session_not_found":
            return JSONResponse(status_code=404, content=error(404, "session_not_found"))
        return JSONResponse(status_code=500, content=error(500, str(e)))
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(result)
