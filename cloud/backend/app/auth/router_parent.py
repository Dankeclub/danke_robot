"""Parent auth routes -- WeChat login, phone binding, token refresh, logout.

Aligned with parent-openapi.yaml v0.2.0-draft.
"""

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.auth.schemas import (
    ParentProfile,
    PhoneBindRequest,
    PhoneBindResponse,
    RefreshTokenRequest,
    TokenPairResponse,
    WechatLoginRequest,
    WechatLoginResponse,
)
from app.auth.security import (
    create_parent_access_token,
    create_refresh_token_record,
    hash_phone,
    mask_phone,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.config import settings
from app.db import get_db
from app.models.parent import ParentAccount
from app.schemas.common import error, ok

parent_auth_router = APIRouter(prefix="/auth", tags=["parent-auth"])


@parent_auth_router.post("/wechat/login")
async def wechat_login(
    body: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """WeChat mini-program login: exchange wx.login() code for JWT.

    1. Call WeChat jscode2session API
    2. Find or create ParentAccount by openid
    3. Issue JWT access + refresh tokens
    """
    wx_appid = body.app_id or settings.wx_appid
    wx_secret = settings.wx_secret.get_secret_value()

    if not wx_appid or not wx_secret:
        return JSONResponse(
            status_code=503,
            content=error(503, "wechat_not_configured"),
        )

    # Call WeChat API
    wx_url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={wx_appid}&secret={wx_secret}"
        f"&js_code={body.wx_code}&grant_type=authorization_code"
    )

    try:
        async with httpx.AsyncClient() as client:
            wx_resp = await client.get(wx_url, timeout=10.0)
            wx_data = wx_resp.json()
    except httpx.HTTPError:
        return JSONResponse(
            status_code=502,
            content=error(502, "wechat_service_unavailable"),
        )

    wx_openid = wx_data.get("openid")
    if not wx_openid:
        wx_err_code = wx_data.get("errcode", "unknown")
        return JSONResponse(
            status_code=401,
            content=error(401, f"wechat_code_invalid: {wx_err_code}"),
        )

    wx_unionid = wx_data.get("unionid")

    # Find or create parent account
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.wx_openid == wx_openid)
    )
    parent = result.scalar_one_or_none()

    is_new_user = False
    if parent is None:
        is_new_user = True
        parent = ParentAccount(
            wx_openid=wx_openid,
            wx_unionid=wx_unionid,
            status="pending_bind",
        )
        db.add(parent)
        await db.flush()

    need_bind_phone = parent.phone_hash is None

    # Issue tokens
    access_token = create_parent_access_token(parent_id=str(parent.id))
    refresh_token_raw = await create_refresh_token_record(
        db,
        parent_id=str(parent.id),
    )

    await db.commit()

    profile = None
    if not need_bind_phone:
        profile = ParentProfile(
            parent_id=str(parent.id),
            nickname=parent.nickname,
            avatar_url=parent.avatar_url,
            phone_masked=parent.phone_masked,
        )

    return ok(
        WechatLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=7200,
            is_new_user=is_new_user,
            need_bind_phone=need_bind_phone,
            profile=profile,
        ).model_dump()
    )


@parent_auth_router.post("/phone/bind")
async def bind_phone(
    body: PhoneBindRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Bind phone number to parent account (after WeChat login).

    Phase 1 simplified: plaintext phone input via body.phone.
    Future: exchange body.wx_bind_token via WeChat API for phone number.
    """
    # Determine phone input source
    phone = body.phone
    if not phone:
        return JSONResponse(
            status_code=400,
            content=error(400, "phone_required"),
        )

    # Check if phone already bound to another account
    phone_hash = hash_phone(phone)
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.phone_hash == phone_hash)
    )
    existing = result.scalar_one_or_none()
    if existing and str(existing.id) != parent_id:
        return JSONResponse(
            status_code=409,
            content=error(409, "phone_already_bound"),
        )

    # Update parent account
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.id == parent_id)
    )
    parent = result.scalar_one_or_none()
    if parent is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "parent_not_found"),
        )

    parent.phone_e164 = phone
    parent.phone_hash = phone_hash
    parent.phone_masked = mask_phone(phone)
    parent.status = "active"
    await db.commit()
    await db.refresh(parent)

    profile = ParentProfile(
        parent_id=str(parent.id),
        nickname=parent.nickname,
        avatar_url=parent.avatar_url,
        phone_masked=parent.phone_masked,
    )

    return ok(PhoneBindResponse(profile=profile).model_dump())


@parent_auth_router.post("/token/refresh")
async def parent_refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token -- revoke old, issue new pair."""
    try:
        new_raw, new_record = await rotate_refresh_token(db, body.refresh_token)
    except ValueError as e:
        msg = str(e)
        if msg == "refresh_token_replayed":
            return JSONResponse(
                status_code=401,
                content=error(401, "token_replayed"),
            )
        return JSONResponse(
            status_code=401,
            content=error(401, "invalid_refresh_token"),
        )

    access_token = create_parent_access_token(
        parent_id=str(new_record.parent_id) if new_record.parent_id else "",
    )

    await db.commit()

    return ok(
        TokenPairResponse(
            access_token=access_token,
            refresh_token=new_raw,
            expires_in=7200,
        ).model_dump()
    )


@parent_auth_router.post("/logout")
async def parent_logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token (logout)."""
    await revoke_refresh_token(db, body.refresh_token)
    await db.commit()
    return ok()
