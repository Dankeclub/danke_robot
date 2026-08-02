"""Navigation instruction model — parent remote control."""

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


class NavigationInstruction(Base):
    """A remote navigation instruction from parent to child's car device.

    destination: learning | chat | parent_messages
    status: pending (not yet delivered) | delivered (car acked) | expired (ttl exceeded)
    """

    __tablename__ = "navigation_instruction"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    destination: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "destination IN ('learning','chat','parent_messages')",
            name="ck_nav_destination",
        ),
        nullable=False,
    )
    route_key: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_batch_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('pending','delivered','expired')",
            name="ck_nav_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_nav_child", "child_id"),
        Index("idx_nav_child_status", "child_id", "status"),
    )
