"""Shared parent business logic — access checks, timezone helpers."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parent_child import ParentChild


async def verify_parent_access(
    db: AsyncSession, parent_id: str, child_id: str,
) -> bool:
    """Verify parent has an active binding to the given child."""
    result = await db.execute(
        select(ParentChild).where(
            ParentChild.parent_id == parent_id,
            ParentChild.child_id == child_id,
            ParentChild.status == "active",
        )
    )
    return result.scalar_one_or_none() is not None


def today_shanghai() -> date:
    """Return today's date in Asia/Shanghai timezone."""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).date()


def datetime_range_shanghai(d: date) -> tuple[datetime, datetime]:
    """Return [start_of_day, start_of_next_day) in Asia/Shanghai TZ."""
    tz = timezone(timedelta(hours=8))
    start = datetime(d.year, d.month, d.day, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end
