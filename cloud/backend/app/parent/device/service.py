"""Parent device management business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_binding import DeviceBinding
from app.parent.service import verify_parent_access


def _serialize_device(device: DeviceBinding) -> dict:
    """Serialize a DeviceBinding row to the standard API dict shape."""
    return {
        "device_id": device.device_id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "platform": device.platform,
        "app_version": device.app_version,
        "online": False,
        "last_online_at": None,
        "bound_at": device.bound_at.isoformat() if device.bound_at else None,
        "bind_status": device.bind_status,
        "battery_level": None,
        "signal_strength": None,
        "connection_type": None,
        "current_zone": None,
    }


async def get_device(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    """Get the active device bound to a child."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.child_id == child_id,
            DeviceBinding.bind_status == "active",
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        return None

    return _serialize_device(device)


async def update_device(
    db: AsyncSession, parent_id: str, child_id: str, device_name: str,
) -> dict | None:
    """Update the device name."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.child_id == child_id,
            DeviceBinding.bind_status == "active",
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        return None

    device.device_name = device_name
    await db.flush()

    return _serialize_device(device)


async def unbind_device(
    db: AsyncSession, parent_id: str, child_id: str,
) -> bool:
    """Deactivate the device binding. Returns True if found and deactivated."""
    if not await verify_parent_access(db, parent_id, child_id):
        return False

    result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.child_id == child_id,
            DeviceBinding.bind_status == "active",
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        return False

    device.bind_status = "inactive"
    await db.flush()
    return True


async def bind_device(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    bind_method: str,
    device_id: str | None = None,
    device_code: str | None = None,
    device_name: str | None = None,
) -> dict:
    """Bind a new device to a child.

    Raises ValueError on conflict or access issues.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        raise ValueError("child_not_found")

    # Resolve device_id (Phase 1: device_code is used as device_id)
    resolved_id = device_id or device_code
    if not resolved_id:
        raise ValueError("device_id_required")

    # Check device_id not already bound (active)
    existing = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.device_id == resolved_id,
            DeviceBinding.bind_status == "active",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("device_already_bound")

    # Check child doesn't already have an active device
    child_device = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.child_id == child_id,
            DeviceBinding.bind_status == "active",
        )
    )
    if child_device.scalar_one_or_none() is not None:
        raise ValueError("child_has_device")

    binding = DeviceBinding(
        device_id=resolved_id,
        child_id=child_id,
        device_name=device_name or resolved_id,
        device_type="car",
        bind_status="active",
    )
    db.add(binding)
    await db.flush()

    return _serialize_device(binding)
