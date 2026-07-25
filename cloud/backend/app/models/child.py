"""Child model."""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class Child(Base, AuditMixin):
    """A child profile managed by parents.

    Children do not have login credentials — they are pure profiles
    managed through parent accounts. Devices bind to children, not parents.
    """

    __tablename__ = "child"

    family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("family.id"), nullable=False
    )
    nickname: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(
        Text,
        CheckConstraint(
            "gender IN ('boy', 'girl', 'unknown')",
            name="ck_child_gender",
        ),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_child_family", "family_id"),
    )
