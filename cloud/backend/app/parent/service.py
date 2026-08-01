"""Shared parent business logic — access checks, serialization helpers."""

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
