"""FastAPI dependencies for auth — extract identity from Bearer token."""

import jwt as pyjwt
from fastapi import HTTPException, Request

from app.auth.security import decode_token
from app.schemas.common import error


async def get_current_device(
    request: Request,
) -> dict[str, str]:
    """Extract device identity from Bearer token in Authorization header.

    Returns: {"device_id": str, "child_id": str, "family_id": str}

    Raises HTTPException 401 on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise _unauthorized("missing_token")

    token = auth_header[7:]  # strip "Bearer "
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        raise _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        raise _unauthorized("invalid_token")

    if payload.get("sub_type") != "device":
        raise _unauthorized("wrong_token_type")

    return {
        "device_id": payload["sub"],
        "child_id": payload.get("child_id", ""),
        "family_id": payload.get("family_id", ""),
    }


async def get_current_parent(
    request: Request,
) -> str:
    """Extract parent identity from Bearer token.

    Returns: parent_id as string.

    Raises HTTPException 401 on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise _unauthorized("missing_token")

    token = auth_header[7:]
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        raise _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        raise _unauthorized("invalid_token")

    if payload.get("sub_type") != "parent":
        raise _unauthorized("wrong_token_type")

    return payload["sub"]


def _unauthorized(msg: str):
    """Raise HTTPException with 401 status and consistent error body."""
    return HTTPException(
        status_code=401,
        detail=error(401, msg),
    )
