"""Parent notification schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

DEFAULT_SETTINGS = {
    "task_completed": True, "task_expired": True,
    "child_replied": True, "behavior_alert": True,
    "realtime_alert": True, "goal_achieved": True,
    "daily_summary": True, "weekly_report": True,
    "device_offline": True, "learning_milestone": False,
}


class DndSettings(BaseModel):
    enabled: bool = False
    start_time: str = "22:00"
    end_time: str = "08:00"


class UpdateNotificationSettingsRequest(BaseModel):
    settings: dict = Field(default_factory=dict)
    dnd: DndSettings = Field(default_factory=DndSettings)


class NotificationSettingsOut(BaseModel):
    child_id: str
    settings: dict
    dnd: DndSettings
    updated_at: datetime | None = None


class NotificationItem(BaseModel):
    notification_id: str
    type: str
    icon: str = ""
    title: str
    description: str
    child_id: str
    child_nickname: str = ""
    is_read: bool = False
    created_at: datetime


class PaginatedNotifications(BaseModel):
    unread_count: int = 0
    items: list[NotificationItem] = []
    pagination: dict
