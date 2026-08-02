"""Parent file schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class UploadInitRequest(BaseModel):
    purpose: str = Field(
        ...,
        pattern=r"^(parent_message_image|parent_message_audio|parent_avatar|child_avatar)$",
    )
    file_name: str
    content_type: str
    size_bytes: int = Field(..., gt=0)
    sha256: str


class UploadInitOut(BaseModel):
    upload_id: str
    upload_path: str
    expires_at: datetime


class UploadCompleteRequest(BaseModel):
    size_bytes: int = Field(..., gt=0)
    sha256: str


class FileAccessOut(BaseModel):
    file_id: str
    url: str
    expires_at: datetime
