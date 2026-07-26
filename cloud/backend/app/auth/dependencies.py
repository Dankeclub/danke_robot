"""FastAPI dependencies for auth — extract identity from Bearer token."""

import jwt as pyjwt

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token
from app.db import get_db
from app.schemas.common import error


async def get_current_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Extract device identity from Bearer token in Authorization header.

    Returns: {"device_id": str, "child_id": str, "family_id": str}

    Raises 401 JSONResponse on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _unauthorized("missing_token")

    token = auth_header[7:]  # strip "Bearer "
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        return _unauthorized("invalid_token")

    if payload.get("sub_type") != "device":
        return _unauthorized("wrong_token_type")

    return {
        "device_id": payload["sub"],
        "child_id": payload.get("child_id", ""),
        "family_id": payload.get("family_id", ""),
    }


async def get_current_parent(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """Extract parent identity from Bearer token.

    Returns: parent_id as string.

    Raises 401 JSONResponse on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _unauthorized("missing_token")

    token = auth_header[7:]
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        return _unauthorized("invalid_token")

    if payload.get("sub_type") != "parent":
        return _unauthorized("wrong_token_type")

    return payload["sub"]


def _unauthorized(msg: str):
    """Return a 401 JSONResponse. Never returns — the caller should return this."""
    return JSONResponse(
        status_code=401,
        content=error(401, msg),
    )
