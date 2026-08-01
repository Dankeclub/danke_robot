"""Device binding model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DDL,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class DeviceBinding(Base, AuditMixin):
    """Binding between a child and a device.

    A child can have at most one active device binding at a time.
    Historical bindings (inactive/revoked) are preserved for audit.

    The partial unique index on (child_id) WHERE bind_status = 'active'
    is created in the migration via raw SQL; it cannot be declared in
    SQLAlchemy ORM __table_args__.
    """

    __tablename__ = "device_binding"

    device_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(Text, nullable=False)
    device_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "device_type IN ('car', 'robot')",
            name="ck_device_binding_device_type",
        ),
        nullable=False,
        default="car",
    )
    platform: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    bind_status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "bind_status IN ('active', 'inactive', 'revoked')",
            name="ck_device_binding_bind_status",
        ),
        nullable=False,
        default="active",
    )
    bound_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("idx_device_binding_device", "device_id"),
    )


# DDL event: ensure the partial unique index is created when the table
# is created via Base.metadata.create_all (e.g. in test fixtures).
# The index cannot be declared in __table_args__ because SQLAlchemy
# does not support partial/conditional unique indexes.
event.listen(
    DeviceBinding.__table__,
    "after_create",
    DDL(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_device_binding_child_active "
        "ON device_binding(child_id) WHERE bind_status = 'active'"
    ),
)
