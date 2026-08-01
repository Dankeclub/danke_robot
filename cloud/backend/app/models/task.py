"""Daily learning task model."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class DailyTask(Base):
    """A daily learning task for a child on a specific business date.

    One task per (child_id, business_date, module). Generated on-demand
    or by a scheduled job. Each task holds a config_snapshot so past
    tasks are not affected by config changes.

    Status flow: assigned -> claimed -> in_progress -> completed / expired.
    """

    __tablename__ = "daily_task"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    business_date: Mapped[date] = mapped_column(Date, nullable=False)
    module: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "module IN ('science','math','english','poems','music','quiz')",
            name="ck_task_module",
        ),
        nullable=False,
    )
    task_category: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "task_category IN ('learning','lifestyle','sports','custom')",
            name="ck_task_category",
        ),
        nullable=False,
        default="learning",
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('assigned','claimed','in_progress','completed','expired')",
            name="ck_task_status",
        ),
        nullable=False,
        default="assigned",
    )
    config_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    progress_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
        UniqueConstraint(
            "child_id", "business_date", "module",
            name="uq_task_child_date_module",
        ),
        Index("idx_task_child_date", "child_id", "business_date"),
        Index("idx_task_status", "status"),
    )
