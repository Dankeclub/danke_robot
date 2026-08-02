"""File upload model — metadata for parent-uploaded files (messages, avatars)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FileUpload(Base):
    """Metadata for a file uploaded by a parent.

    Actual file content is stored on local disk (production: OSS/S3).
    status: pending (upload initiated) | available (upload confirmed) | expired (TTL exceeded)
    """

    __tablename__ = "file_upload"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "purpose IN "
            "('parent_message_image','parent_message_audio','parent_avatar','child_avatar')",
            name="ck_file_purpose",
        ),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('pending','available','expired')",
            name="ck_file_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_file_parent", "parent_id"),
        Index("idx_file_status", "status"),
    )
