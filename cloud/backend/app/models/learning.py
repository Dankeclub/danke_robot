"""Learning session, batch, and batch item models.

A learning session is created when the car enters a learning module.
Within a session, batches of content items are issued. Batches are
immutable once created — the car re-fetches the same batch on retry.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LearningSession(Base):
    """A learning session for a child in a specific module.

    Created when the car enters a module via today_task, free_learning,
    task_extension, or ws_navigation. Holds a config_snapshot so that
    parent config changes don't affect in-progress sessions.
    """

    __tablename__ = "learning_session"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "module IN ('science','math','english','poems','music','quiz')",
            name="ck_session_module",
        ),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "source IN ('today_task','free_learning','task_extension','ws_navigation')",
            name="ck_session_source",
        ),
        nullable=False,
    )
    task_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    navigation_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('active','completed','expired')",
            name="ck_session_status",
        ),
        nullable=False,
        default="active",
    )
    config_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_session_child", "child_id"),
        Index("idx_session_module", "module"),
    )


class LearningBatch(Base):
    """An immutable batch of content items within a learning session.

    Content is selected and issued as a batch. The batch is never
    modified — if the car retries, the same batch is returned.
    """

    __tablename__ = "learning_batch"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_session.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(),
    )
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('active','completed')",
            name="ck_batch_status",
        ),
        nullable=False,
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("session_id", "sequence_no", name="uq_batch_session_seq"),
        Index("idx_batch_session", "session_id"),
    )


class BatchItem(Base):
    """A single content item within a learning batch.

    content_type identifies which content table the item came from
    (e.g. 'math_question', 'english_word'). content_snapshot stores
    a frozen copy of the content at the time of issuance, used for
    correct/wrong judging and historical display.
    """

    __tablename__ = "batch_item"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_batch.id"), nullable=False
    )
    content_id: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    content_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    item_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_batch_item_batch", "batch_id"),
    )
