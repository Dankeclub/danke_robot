"""Answer record and wrong answer models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnswerRecord(Base):
    """A single answer submission from the car device.

    Service-side truth: correct_option_id comes from the batch item's
    content_snapshot. The client's selected_option_id is recorded but
    never trusted for correctness.
    """

    __tablename__ = "answer_record"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_session.id"), nullable=False
    )
    batch_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("batch_item.id"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(Text, nullable=False)
    question_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    selected_option_id: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answer_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_answer_session", "session_id"),
        Index("idx_answer_child", "child_id"),
    )


class WrongAnswer(Base):
    """Aggregated wrong answer tracking for review and re-practice.

    Deduplicated by (child_id, question_id). Each subsequent wrong
    answer increments wrong_count and updates last_wrong_at.
    """

    __tablename__ = "wrong_answer"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(Text, nullable=False)
    question_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    question_id: Mapped[str] = mapped_column(Text, nullable=False)
    selected_option_id: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(Text, nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_wrong_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_wrong_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
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
        Index("idx_wrong_answer_child", "child_id"),
        Index("idx_wrong_answer_question", "child_id", "question_id"),
    )
