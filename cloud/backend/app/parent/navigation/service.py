"""Parent navigation business logic."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.navigation import NavigationInstruction
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def create_navigation(
    db: AsyncSession, parent_id: str, child_id: str,
    destination: str, route_key: str,
    module: str | None = None,
    custom_batch_size: int | None = None,
    title: str | None = None,
    expires_in_seconds: int = 600,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    now = datetime.now(SHANGHAI_TZ)
    expires_at = now + timedelta(seconds=expires_in_seconds)
    nav = NavigationInstruction(
        child_id=child_id, parent_id=parent_id,
        destination=destination, route_key=route_key,
        module=module, custom_batch_size=custom_batch_size,
        title=title, expires_at=expires_at, status="pending",
    )
    db.add(nav)
    await db.flush()
    return {
        "navigation_id": str(nav.id),
        "destination": destination, "route_key": route_key,
        "module": module, "custom_batch_size": custom_batch_size,
        "title": title, "expires_at": expires_at,
        "created_at": now,
    }
