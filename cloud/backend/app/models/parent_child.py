"""Parent-child binding model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class ParentChild(Base, AuditMixin):
    """Binding between a parent account and a child.

    A parent can manage multiple children. The same parent-child pair
    must not appear more than once (unique constraint).
    """

    __tablename__ = "parent_child"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("family.id"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        UniqueConstraint("parent_id", "child_id"),
        Index("idx_parent_child_parent", "parent_id"),
        Index("idx_parent_child_child", "child_id"),
    )
