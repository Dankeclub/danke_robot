"""Car parent-message schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageReply(BaseModel):
    reply_id: str
    type: str
    preset_code: str | None = None
    text: str | None = None
    file_id: str | None = None
    duration_ms: int | None = None
    created_at: datetime


class ParentMessageOut(BaseModel):
    message_id: str
    type: str
    content: dict
    created_at: datetime
    replies: list[MessageReply] = []


class ParentMessagesList(BaseModel):
    items: list[ParentMessageOut]


class SendReplyRequest(BaseModel):
    type: str = Field(..., pattern=r"^(preset_text|voice)$")
    preset_code: str | None = Field(
        None,
        pattern=r"^(got_it|will_do_now|done|later|thank_you)$",
    )
    file_id: str | None = None
    duration_ms: int | None = Field(None, gt=0)
