"""Telemetry event ingestion routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.db import get_db
from app.schemas.common import error, ok
from app.telemetry.schemas import BatchEventsRequest
from app.telemetry.service import insert_events

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
    await db.commit()

    return ok({"accepted": accepted, "duplicates": duplicates})
