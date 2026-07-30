"""Parent device management routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.device.schemas import (
    BindDeviceRequest,
    DeviceInfo,
    UpdateDeviceRequest,
)
from app.parent.device.service import (
    bind_device,
    get_device,
    unbind_device,
    update_device,
)
from app.schemas.common import error, ok

device_router = APIRouter(prefix="/children", tags=["parent-device"])


@device_router.get("/{child_id}/device")
async def get_device_endpoint(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get the active device bound to a child."""
    try:
        device = await get_device(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if device is None:
        return JSONResponse(status_code=404, content=error(404, "device_not_found"))

    return ok(DeviceInfo(**device).model_dump())


@device_router.put("/{child_id}/device")
async def update_device_endpoint(
    child_id: str,
    body: UpdateDeviceRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Update device name."""
    try:
        device = await update_device(db, parent_id, child_id, body.device_name)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if device is None:
        return JSONResponse(status_code=404, content=error(404, "device_not_found"))

    return ok(DeviceInfo(**device).model_dump())


@device_router.delete("/{child_id}/device")
async def delete_device_endpoint(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Unbind device from child."""
    try:
        found = await unbind_device(db, parent_id, child_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if not found:
        return JSONResponse(status_code=404, content=error(404, "device_not_found"))

    return ok()


@device_router.post("/{child_id}/device/bind")
async def bind_device_endpoint(
    child_id: str,
    body: BindDeviceRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Bind a new device to a child."""
    try:
        device = await bind_device(
            db,
            parent_id=parent_id,
            child_id=child_id,
            bind_method=body.bind_method,
            device_id=body.device_id,
            device_code=body.device_code,
            device_name=body.device_name,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg == "device_already_bound":
            return JSONResponse(status_code=409, content=error(409, msg))
        if msg in ("child_not_found", "device_id_required", "child_has_device"):
            return JSONResponse(status_code=400, content=error(400, msg))
        return JSONResponse(status_code=400, content=error(400, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    return ok(DeviceInfo(**device).model_dump())
