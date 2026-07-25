"""Parent account model."""

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class ParentAccount(Base, AuditMixin):
    """A parent user account.

    Attributes:
        phone_e164: E.164 formatted phone number.
        phone_hash: Deterministic hash of the phone number, used for lookups.
        phone_masked: Displayable masked phone number.
        nickname: Optional display name.
        avatar_url: Optional avatar image URL.
        wx_openid: WeChat OpenID for this mini-program.
        wx_unionid: WeChat UnionID across apps (optional).
        status: Account status, defaults to 'active'.
    """

    __tablename__ = "parent_account"

    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)
    phone_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    phone_masked: Mapped[str] = mapped_column(Text, nullable=False)
    nickname: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wx_openid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    wx_unionid: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
