"""Auth module request/response pydantic schemas — aligned with parent-openapi.yaml."""

from typing import Literal

from pydantic import BaseModel, Field

# ── Shared ──────────────────────────────────────────────

class ChildProfile(BaseModel):
    """Minimal child profile returned after car login."""
    child_id: str
    nickname: str
    avatar_url: str | None = None
    family_id: str


class ParentProfile(BaseModel):
    """Parent profile returned after WeChat login."""
    parent_id: str
    nickname: str | None = None
    avatar_url: str | None = None
    phone_masked: str | None = None


class TokenPairResponse(BaseModel):
    """Access + refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int = 7200


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh and logout."""
    refresh_token: str


# ── Car login ───────────────────────────────────────────

class CarLoginRequest(BaseModel):
    """Request body for car phone-number login."""
    phone: str = Field(..., description="E.164 phone number, e.g. +8613800138000")
    device_id: str = Field(..., description="Device serial number / unique ID")
    device_name: str = Field(default="蛋仔机器人", description="Human-readable device name")
    device_type: Literal["car", "robot"] = "car"
    app_version: str | None = None


class CarLoginResponse(TokenPairResponse):
    """Car login success response."""
    child_profile: ChildProfile


# ── Parent WeChat login ─────────────────────────────────

class WechatLoginRequest(BaseModel):
    """Request body for parent WeChat mini-program login — aligned with parent-openapi.yaml."""
    wx_code: str = Field(..., alias="wx_code", description="wx.login() temporary code")
    app_id: str = Field(..., description="WeChat Mini Program AppID")
    invite_code: str | None = None

    model_config = {"populate_by_name": True}


class WechatLoginResponse(TokenPairResponse):
    """WeChat login response."""
    is_new_user: bool = False
    need_bind_phone: bool = False
    profile: ParentProfile | None = None


# ── Phone binding ───────────────────────────────────────

class PhoneBindRequest(BaseModel):
    """Request body for binding phone number after WeChat login — aligned with parent-openapi.yaml.

    Priority: plaintext phone (Phase 1 simple flow) > wx_bind_token exchange.
    """
    wx_bind_token: str = Field(
        default="",
        description="WeChat phone bind token from wx.getPhoneNumber() (future)",
    )
    encrypted_data: str | None = None
    iv: str | None = None
    phone: str | None = Field(
        default=None,
        description="Plaintext E.164 phone number (Phase 1 simple flow)",
    )
    verify_code: str | None = None


class PhoneBindResponse(BaseModel):
    """Phone binding success response."""
    profile: ParentProfile
