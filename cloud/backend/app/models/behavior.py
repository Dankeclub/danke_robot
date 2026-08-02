"""Behavior event model — focus, posture, location, zone events from car device."""

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BehaviorEvent(Base):
    """A behavior observation event from the car device.

    Events are produced by the behavioral module on SC171 (MediaPipe + YOLOv8)
    and ingested via telemetry batch endpoint. Each event records a score
    (0-100) and optional payload with detailed metrics.

    event_type determines which analysis page consumes it:
      - focus: attention/focus score
      - posture: sitting posture score
      - location: child's location in room
      - zone: room zone change
    """

    __tablename__ = "behavior_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "event_type IN ('focus','posture','location','zone')",
            name="ck_behavior_event_type",
        ),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Score 0-100, higher is better for focus/posture"
    )
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Detailed metrics: {duration_seconds, zone_name, ...}"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When the behavior was observed (device time)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_behavior_child", "child_id"),
        Index("idx_behavior_child_type_time", "child_id", "event_type", "recorded_at"),
    )
