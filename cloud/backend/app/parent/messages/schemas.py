"""Parent messages schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageReply(BaseModel):
    reply_id: str
    type: str
    preset_code: str | None = None
    text: str | None = None
    created_at: datetime


class MessageOut(BaseModel):
    message_id: str
    direction: str
    type: str
    content: dict
    created_at: datetime
    replies: list[MessageReply] = []


class PaginatedMessages(BaseModel):
    items: list[MessageOut]
    pagination: dict


class SendMessageRequest(BaseModel):
    type: str = Field(..., pattern=r"^(text|image|audio|task_card)$")
    content: dict
