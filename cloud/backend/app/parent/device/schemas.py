"""Parent device management schemas — aligned with parent-openapi.yaml."""

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """Device info returned to parent."""
    device_id: str
    device_name: str
    device_type: str  # car | robot
    platform: str | None = None
    app_version: str | None = None
    online: bool = False
    last_online_at: datetime | None = None
    bound_at: datetime | None = None
    bind_status: str  # active | inactive | revoked
    battery_level: int | None = None
    signal_strength: int | None = None
    connection_type: str | None = None
    current_zone: str | None = None


class UpdateDeviceRequest(BaseModel):
    """Request body for updating device name."""
    device_name: str = Field(..., min_length=1, max_length=50)


class BindDeviceRequest(BaseModel):
    """Request body for binding a device to a child."""
    bind_method: str = Field(..., pattern=r"^(device_code|phone_auto|scan_qr)$")
    device_code: str | None = None
    device_id: str | None = None
    device_name: str | None = None
