"""Parent online status schemas."""

from datetime import datetime

from pydantic import BaseModel


class OnlineStatusOut(BaseModel):
    online: bool = False
    ws_connected: bool = False
    last_seen_at: datetime | None = None
    current_zone: str | None = None
    current_route_key: str | None = None
    current_activity: str | None = None
