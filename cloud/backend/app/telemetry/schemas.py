"""Telemetry request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class EventItem(BaseModel):
    """A single telemetry event from the car device."""
    event_id: str = Field(..., description="UUID v4 idempotency key")
    event_type: str = Field(..., description="e.g. learning.session.start")
    module: str | None = Field(None, description="Learning module: science, math, etc.")
    timestamp: datetime = Field(..., description="Event occurrence time (ISO 8601 with offset)")
    payload: dict = Field(default_factory=dict, description="Arbitrary event data")


class BatchEventsRequest(BaseModel):
    """Batch event upload request."""
    events: list[EventItem] = Field(..., min_length=1, max_length=100)


class BatchEventsResponse(BaseModel):
    """Batch event upload response."""
    accepted: int = Field(..., description="Number of events accepted")
    duplicates: int = Field(default=0, description="Number of duplicate events skipped")
