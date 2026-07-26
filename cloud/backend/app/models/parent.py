"""Parent account model."""

from sqlalchemy import DDL, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class ParentAccount(Base, AuditMixin):
    """A parent user account.

    Phone fields are nullable to support WeChat-first registration:
    wx.login() creates an account with status='pending_bind', then
    phone is bound later via /auth/phone/bind.

    Attributes:
        phone_e164: E.164 formatted phone number (nullable).
        phone_hash: Deterministic hash of the phone number (nullable).
        phone_masked: Displayable masked phone number (nullable).
        nickname: Optional display name.
        avatar_url: Optional avatar image URL.
        wx_openid: WeChat OpenID for this mini-program (nullable).
        wx_unionid: WeChat UnionID across apps (nullable).
        status: 'active' | 'pending_bind' | 'disabled'.
    """

    __tablename__ = "parent_account"

    phone_e164: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_masked: Mapped[str | None] = mapped_column(Text, nullable=True)
    nickname: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wx_openid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    wx_unionid: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
    )


# DDL event: create conditional unique index on phone_hash.
# SQLAlchemy ORM does not support WHERE clauses on UniqueConstraint,
# so we register it as a raw DDL after_create event.
event.listen(
    ParentAccount.__table__,
    "after_create",
    DDL(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_parent_account_phone_hash "
        "ON parent_account(phone_hash) WHERE phone_hash IS NOT NULL"
    ),
)
