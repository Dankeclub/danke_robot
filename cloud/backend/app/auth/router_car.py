"""Car device auth routes — phone number login, token refresh, logout."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    CarLoginRequest,
    CarLoginResponse,
    ChildProfile,
    RefreshTokenRequest,
    TokenPairResponse,
)
from app.auth.security import (
    check_phone_login_rate_limit,
    create_access_token,
    create_refresh_token_record,
    hash_phone,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.db import get_db
from app.models.child import Child
from app.models.device_binding import DeviceBinding
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.schemas.common import error, ok

car_auth_router = APIRouter(prefix="/auth", tags=["car-auth"])


@car_auth_router.post("/login")
async def car_phone_login(
    body: CarLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login with phone number for car device.

    1. Rate-limit by client IP
    2. Hash phone → find ParentAccount
    3. Resolve child via ParentChild (is_default=True)
    4. Create/update DeviceBinding
    5. Issue JWT access + refresh tokens
    6. Return CarLoginResponse
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit
    try:
        check_phone_login_rate_limit(client_ip)
    except ValueError:
        return JSONResponse(
            status_code=429,
            content=error(429, "rate_limit_exceeded"),
        )

    # Find parent by phone hash
    phone_hash = hash_phone(body.phone)
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.phone_hash == phone_hash)
    )
    parent = result.scalar_one_or_none()

    if parent is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "phone_not_bound"),
        )

    if parent.status != "active":
        return JSONResponse(
            status_code=403,
            content=error(403, "account_disabled"),
        )

    # Find default child
    # TODO: support multi-child selection on car login
    result = await db.execute(
        select(ParentChild, Child, Family)
        .join(Child, ParentChild.child_id == Child.id)
        .join(Family, Child.family_id == Family.id)
        .where(
            ParentChild.parent_id == parent.id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "no_child_found"),
        )

    _pc, child, family = row

    # Create or update device binding
    result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.device_id == body.device_id,
        )
    )
    binding = result.scalar_one_or_none()

    if binding is None:
        # Deactivate any existing active binding for this child
        result = await db.execute(
            select(DeviceBinding).where(
                DeviceBinding.child_id == child.id,
                DeviceBinding.bind_status == "active",
            )
        )
        old_binding = result.scalar_one_or_none()
        if old_binding:
            old_binding.bind_status = "inactive"

        binding = DeviceBinding(
            device_id=body.device_id,
            child_id=child.id,
            device_name=body.device_name,
            device_type=body.device_type,
            app_version=body.app_version,
            bind_status="active",
            bound_at=datetime.now(UTC),
        )
        db.add(binding)
    else:
        binding.device_name = body.device_name
        binding.device_type = body.device_type
        binding.app_version = body.app_version
        binding.bind_status = "active"

    await db.flush()

    # Issue tokens
    access_token = create_access_token(
        device_id=binding.device_id,
        child_id=str(child.id),
        family_id=str(family.id),
    )
    refresh_token_raw = await create_refresh_token_record(
        db,
        device_id=binding.device_id,
        child_id=str(child.id),
        family_id=str(family.id),
    )

    await db.commit()

    return ok(
        CarLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=7200,
            child_profile=ChildProfile(
                child_id=str(child.id),
                nickname=child.nickname,
                avatar_url=child.avatar_url,
                family_id=str(family.id),
            ),
        ).model_dump()
    )


@car_auth_router.post("/refresh")
async def car_refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token — revoke old, issue new pair."""
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

    # Issue new access token
    access_token = create_access_token(
        device_id=new_record.device_id or "",
        child_id=str(new_record.child_id) if new_record.child_id else "",
        family_id=str(new_record.family_id) if new_record.family_id else "",
    )

    await db.commit()

    return ok(
        TokenPairResponse(
            access_token=access_token,
            refresh_token=new_raw,
            expires_in=7200,
        ).model_dump()
    )


@car_auth_router.post("/logout")
async def car_logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token (logout)."""
    await revoke_refresh_token(db, body.refresh_token)
    await db.commit()
    return ok()
