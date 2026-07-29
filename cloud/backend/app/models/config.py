"""Learning module configuration model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LearningModuleConfig(Base):
    """Per-child, per-module learning configuration.

    A default config is seeded for each (child, module) pair. Parents can
    modify enabled, difficulty/category, batch_size, and
    min_repeat_interval_seconds. Each modification increments config_version.

    The car reads the current config via GET /learning/park (ConfigSnapshot).
    """

    __tablename__ = "learning_module_config"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    module: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "module IN ('science','math','english','poems','music','quiz')",
            name="ck_config_module",
        ),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    difficulty: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    min_repeat_interval_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=604800
    )
    config_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
        UniqueConstraint("child_id", "module", name="uq_config_child_module"),
        Index("idx_config_child", "child_id"),
    )
