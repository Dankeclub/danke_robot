"""Parent children management schemas — aligned with parent-openapi.yaml."""

from datetime import date

from pydantic import BaseModel, Field

# ── Child Summary ───────────────────────────────────────

class ChildSummary(BaseModel):
    """Child list item returned to parent."""
    child_id: str
    nickname: str
    avatar_url: str | None = None
    birth_date: date | None = None
    gender: str | None = None  # boy | girl | unknown
    family_id: str
    family_name: str
    is_default: bool = False


# ── Device Summary (embedded in child detail) ───────────

class DeviceInfoBrief(BaseModel):
    """Minimal device info embedded in child detail."""
    device_id: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    online: bool = False
    bind_status: str | None = None


# ── Child Detail ────────────────────────────────────────

class ChildDetail(ChildSummary):
    """Child detail with device info."""
    device: DeviceInfoBrief | None = None


# ── Create Child ────────────────────────────────────────

class CreateChildRequest(BaseModel):
    """Request body for creating a child."""
    nickname: str = Field(..., min_length=1, max_length=50)
    avatar_url: str | None = None
    birth_date: date | None = None
    gender: str | None = Field(default=None, pattern=r"^(boy|girl|unknown)$")
    family_id: str | None = Field(
        default=None,
        description="Family UUID; a new family is created automatically if null or empty",
    )


# ── Update Child ────────────────────────────────────────

class UpdateChildRequest(BaseModel):
    """Request body for updating a child."""
    nickname: str = Field(..., min_length=1, max_length=50)
    avatar_url: str | None = None
    birth_date: date | None = None
    gender: str | None = Field(default=None, pattern=r"^(boy|girl|unknown)$")
