"""Parent navigation schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class NavigationRequest(BaseModel):
    destination: str = Field(..., pattern=r"^(learning|chat|parent_messages)$")
    route_key: str
    module: str | None = None
    custom_batch_size: int | None = Field(default=None, ge=1, le=20)
    title: str | None = None
    expires_in_seconds: int = Field(default=600, ge=60, le=3600)


class NavigationOut(BaseModel):
    navigation_id: str
    destination: str
    route_key: str
    module: str | None = None
    custom_batch_size: int | None = None
    title: str | None = None
    expires_at: datetime
    created_at: datetime
