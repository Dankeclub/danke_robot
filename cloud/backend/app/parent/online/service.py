"""Parent online status — in-memory cache for Phase 3, Redis for Phase 4."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.parent.service import verify_parent_access

# TODO(Phase 4): Migrate _online_store from in-memory dict to Redis.
# In-memory storage does not survive process restarts and cannot be
# shared across multiple backend instances. Redis will provide:
#   - Persistence across deployments/restarts
#   - Shared state for horizontally scaled backend pods
#   - TTL-based auto-expiry (replace the manual 300s timeout logic)
# Use a key pattern like online_status:{child_id} with a 5-minute TTL
# refreshed on each heartbeat.
_online_store: dict[str, dict] = {}
SHANGHAI_TZ = timezone(timedelta(hours=8))


async def get_online_status(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    status = _online_store.get(child_id)
    if status is None:
        return {
            "online": False, "ws_connected": False,
            "last_seen_at": None, "current_zone": None,
            "current_route_key": None, "current_activity": None,
        }
    last = status.get("updated_at")
    if last and (datetime.now(SHANGHAI_TZ) - last).total_seconds() > 300:
        status["online"] = False
        status["ws_connected"] = False
    return {
        "online": status.get("online", False),
        "ws_connected": status.get("ws_connected", False),
        "last_seen_at": status.get("last_seen_at"),
        "current_zone": status.get("current_zone"),
        "current_route_key": status.get("current_route_key"),
        "current_activity": status.get("current_activity"),
    }


def update_online_status(child_id: str, **kwargs) -> None:
    """Update in-memory online status for a child (called by car heartbeat)."""
    if child_id not in _online_store:
        _online_store[child_id] = {}
    _online_store[child_id].update(kwargs)
    _online_store[child_id]["updated_at"] = datetime.now(SHANGHAI_TZ)
