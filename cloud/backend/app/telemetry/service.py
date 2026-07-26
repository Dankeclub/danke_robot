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
    accepted = 0
    duplicates = 0

    for event in events:
        stmt = (
            pg_insert(LearningEvent)
            .values(
                device_id=device_id,
                child_id=child_id,
                event_id=event["event_id"],
                event_type=event["event_type"],
                module=event.get("module"),
                timestamp=event["timestamp"],
                payload=event.get("payload", {}),
            )
            .on_conflict_do_nothing(
                index_elements=["device_id", "event_id"],
            )
        )
        result = await db.execute(stmt)
        if result.rowcount and result.rowcount > 0:
            accepted += 1
        else:
            duplicates += 1

    await db.flush()
    return accepted, duplicates
