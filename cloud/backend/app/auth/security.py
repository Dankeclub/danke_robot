"""JWT token creation, verification, rotation, and rate limiting."""

import hashlib
import hmac
import secrets
import time
import uuid
from datetime import UTC, datetime

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.config import settings

# ── Hashing ─────────────────────────────────────────────

_PHONE_PEPPER = "danke-phone-pepper-v1"  # TODO: move to config
_TOKEN_PEPPER = "danke-token-pepper-v1"  # TODO: move to config


def hash_token(token: str) -> str:
    """HMAC-SHA256 hash of a token string with server-side pepper."""
    return hmac.new(
        _TOKEN_PEPPER.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


def hash_phone(phone: str) -> str:
    """HMAC-SHA256 hash of phone number with server-side pepper."""
    return hmac.new(
        _PHONE_PEPPER.encode(),
        phone.encode(),
        hashlib.sha256,
    ).hexdigest()


# ── JWT ─────────────────────────────────────────────────

def _base_payload(scope: str) -> dict:
    """Common JWT claims."""
    now = int(time.time())
    return {
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
        "iss": "danke-backend",
        "scope": scope,
    }


def create_access_token(
    device_id: str,
    child_id: str,
    family_id: str,
    scope: str = (
        "car.learning.read car.learning.write car.chat "
        "car.messages car.files car.realtime"
    ),
) -> str:
    """Sign a JWT access token for the car device."""
    payload = {
        **_base_payload(scope),
        "sub": device_id,
        "child_id": child_id,
        "family_id": family_id,
        "sub_type": "device",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_parent_access_token(
    parent_id: str,
    scope: str = "parent.read parent.write parent.manage",
) -> str:
    """Sign a JWT access token for a parent (WeChat login)."""
    payload = {
        **_base_payload(scope),
        "sub": parent_id,
        "sub_type": "parent",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "jti", "sub", "scope"]},
    )


# ── Phone hash ──────────────────────────────────────────

def mask_phone(phone: str) -> str:
    """Mask phone number for display: +8613800138000 -> 138****8000."""
    digits = phone.replace("+", "").replace("86", "", 1) if phone.startswith("+86") else phone
    if len(digits) >= 7:
        return f"{digits[:3]}****{digits[-4:]}"
    return digits


# ── Refresh token management ────────────────────────────

def _generate_refresh_token_raw() -> str:
    """Generate a cryptographically random refresh token string."""
    return secrets.token_urlsafe(48)


async def create_refresh_token_record(
    db: AsyncSession,
    *,
    parent_id: str | None = None,
    device_id: str | None = None,
    child_id: str | None = None,
    family_id: str | None = None,
) -> str:
    """Create a RefreshToken row and return the raw token."""
    raw = _generate_refresh_token_raw()
    token_hash = hash_token(raw)
    expires_at = datetime.now(UTC).timestamp() + settings.refresh_token_ttl_seconds

    record = RefreshToken(
        token_hash=token_hash,
        parent_id=uuid.UUID(parent_id) if parent_id else None,
        device_id=device_id,
        child_id=uuid.UUID(child_id) if child_id else None,
        family_id=uuid.UUID(family_id) if family_id else None,
        expires_at=datetime.fromtimestamp(expires_at, tz=UTC),
    )
    db.add(record)
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    old_raw_token: str,
) -> tuple[str, RefreshToken]:
    """Rotate a refresh token: revoke old, create new, detect replay.

    Returns (new_raw_token, new_record).

    If the old token was already revoked, revokes the entire rotation
    chain (replay detection) and raises ValueError.
    """
    old_hash = hash_token(old_raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    )
    old_record = result.scalar_one_or_none()

    if old_record is None:
        raise ValueError("refresh_token_not_found")

    if old_record.revoked_at is not None:
        # Replay detected -- revoke entire chain
        await _revoke_chain(db, old_record)
        await db.commit()
        raise ValueError("refresh_token_replayed")

    # Revoke old token
    old_record.revoked_at = datetime.now(UTC)

    # Create new token, rotated from old
    new_raw = _generate_refresh_token_raw()
    new_hash = hash_token(new_raw)
    expires_at = datetime.now(UTC).timestamp() + settings.refresh_token_ttl_seconds

    new_record = RefreshToken(
        token_hash=new_hash,
        parent_id=old_record.parent_id,
        device_id=old_record.device_id,
        child_id=old_record.child_id,
        family_id=old_record.family_id,
        expires_at=datetime.fromtimestamp(expires_at, tz=UTC),
        rotated_from_id=old_record.id,
    )
    db.add(new_record)
    await db.flush()
    return new_raw, new_record


async def _revoke_chain(db: AsyncSession, record: RefreshToken) -> None:
    """Recursively revoke all tokens in the rotation chain."""
    now = datetime.now(UTC)
    record.revoked_at = now
    if record.rotated_from_id:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.id == record.rotated_from_id)
        )
        parent = result.scalar_one_or_none()
        if parent and parent.revoked_at is None:
            await _revoke_chain(db, parent)


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    """Revoke a refresh token by its raw value."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        await db.flush()


# ── Rate limiting (in-memory, single-worker only) ───────
# TODO: Replace with Redis-based rate limiter (lua script / sliding window)
# when multi-worker deployment is needed.

_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_check_count: int = 0


def check_phone_login_rate_limit(ip: str) -> None:
    """Check rate limit for phone login. Raises ValueError if exceeded.

    Single-worker only -- each worker has its own in-memory counter.
    Docker Compose must use --workers 1.
    """
    global _rate_limit_check_count
    _rate_limit_check_count += 1

    now = time.time()
    window_start = now - 60  # 1 minute sliding window

    # Periodic cleanup of stale IP entries (every 100 checks)
    if _rate_limit_check_count % 100 == 0:
        stale_ips = [
            ip_addr for ip_addr, timestamps in _rate_limit_store.items()
            if not timestamps or all(ts <= window_start for ts in timestamps)
        ]
        for ip_addr in stale_ips:
            del _rate_limit_store[ip_addr]

    # Clean old entries for this IP
    if ip in _rate_limit_store:
        _rate_limit_store[ip] = [
            ts for ts in _rate_limit_store[ip] if ts > window_start
        ]
    else:
        _rate_limit_store[ip] = []

    if len(_rate_limit_store[ip]) >= settings.phone_login_rate_limit:
        raise ValueError("rate_limit_exceeded")

    _rate_limit_store[ip].append(now)
