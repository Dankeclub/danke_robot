"""Family model."""

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class Family(Base, AuditMixin):
    """A family group that parents and children belong to.

    Phase 1 is intentionally minimal — only a name. Multi-parent support
    and family-level settings are deferred to later phases.
    """

    __tablename__ = "family"

    name: Mapped[str] = mapped_column(Text, nullable=False)
