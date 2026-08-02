"""Parent-child message model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ParentMessage(Base):
    """A message between parent and child.

    direction: parent_to_child | child_to_parent
    msg_type: text | image | audio | task_card
    content is a JSONB blob whose schema depends on msg_type.
    """

    __tablename__ = "parent_message"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "direction IN ('parent_to_child','child_to_parent')",
            name="ck_msg_direction",
        ),
        nullable=False,
    )
    msg_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "msg_type IN ('text','image','audio','task_card','preset_text','voice')",
            name="ck_msg_type",
        ),
        nullable=False,
    )
    content: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Schema varies by msg_type: {text}, {file_id, playback_url}, {task_id, ...}"
    )
    replied_to_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("parent_message.id"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_msg_child", "child_id"),
        Index("idx_msg_child_parent", "child_id", "parent_id"),
        Index("idx_msg_created", "created_at"),
    )
