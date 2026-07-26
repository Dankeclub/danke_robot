"""Refresh token model for JWT token rotation."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RefreshToken(Base):
    """Stores hashed refresh tokens for JWT rotation.

    parent_id and device_id are mutually exclusive — car login stores
    device_id; parent login stores parent_id. This is enforced at the
    application layer, not via DB constraint.
    """

    __tablename__ = "refresh_token"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    token_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parent_account.id"),
        nullable=True,
    )
    device_id: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("device_binding.device_id"),
        nullable=True,
    )
    child_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child.id"),
        nullable=True,
    )
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family.id"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotated_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_token.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
