"""Telemetry event ingestion with idempotency."""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.telemetry.models import LearningEvent


async def insert_events(
    db: AsyncSession,
    device_id: str,
    child_id: str,
    events: list[dict],
) -> tuple[int, int]:
    """Insert events with idempotency. Returns (accepted, duplicates).

    Uses PostgreSQL ON CONFLICT DO NOTHING for idempotent inserts.
    Duplicate (device_id, event_id) pairs are silently skipped.
    """
    if not events:
        return 0, 0

    values = [
        {
            "device_id": device_id,
            "child_id": child_id,
            "event_id": e["event_id"],
            "event_type": e["event_type"],
            "module": e.get("module"),
            "timestamp": e["timestamp"],
            "payload": e.get("payload", {}),
        }
        for e in events
    ]

    stmt = (
        pg_insert(LearningEvent)
        .values(values)
        .on_conflict_do_nothing(index_elements=["device_id", "event_id"])
    )
    result = await db.execute(stmt)
    # ON CONFLICT DO NOTHING: rowcount counts only inserted rows
    accepted = result.rowcount or 0
    duplicates = len(events) - accepted
    await db.flush()
    return accepted, duplicates
