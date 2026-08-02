"""Car file service — upload init, complete, access.

Reuses app/models/file_upload.py. Car device uploads resolve parent_id from
the child's ParentChild binding so the existing FileUpload.parent_id FK works.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload
from app.models.parent_child import ParentChild

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def _resolve_parent_id(db: AsyncSession, child_id: str) -> str | None:
    """Find the default parent_id for a child via ParentChild binding."""
    result = await db.execute(
        select(ParentChild.parent_id).where(
            ParentChild.child_id == child_id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.first()
    return str(row[0]) if row else None


async def init_upload(
    db: AsyncSession,
    child_id: str,
    purpose: str,
    file_name: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
) -> dict:
    """Initiate a file upload for a car device.

    Resolves the parent_id from child's default parent binding so the
    FileUpload record links to a valid parent_account.id FK.
    """
    parent_id = await _resolve_parent_id(db, child_id)
    if parent_id is None:
        raise ValueError("no_parent_binding")

    upload_id = uuid.uuid4()
    ext = os.path.splitext(file_name)[1] or ""
    storage_path = f"{purpose}/{upload_id}{ext}"
    expires_at = datetime.now(SHANGHAI_TZ) + timedelta(hours=1)

    record = FileUpload(
        id=upload_id,
        parent_id=uuid.UUID(parent_id),
        purpose=purpose,
        file_name=file_name,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        storage_path=storage_path,
        status="pending",
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()
    return {
        "upload_id": str(upload_id),
        "upload_path": storage_path,
        "expires_at": expires_at,
    }


async def _get_parent_id_for_child(db: AsyncSession, child_id: str) -> uuid.UUID | None:
    """Resolve parent UUID for a child."""
    result = await db.execute(
        select(ParentChild.parent_id).where(
            ParentChild.child_id == child_id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.first()
    return row[0] if row else None


async def complete_upload(
    db: AsyncSession,
    child_id: str,
    upload_id: str,
    size_bytes: int,
    sha256: str,
) -> dict | None:
    """Confirm upload completion. Marks file as available.

    Verifies the file belongs to this child by resolving child→parent binding.
    """
    parent_uuid = await _get_parent_id_for_child(db, child_id)
    if parent_uuid is None:
        return None

    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        return None

    result = await db.execute(
        select(FileUpload).where(
            FileUpload.id == uid,
            FileUpload.parent_id == parent_uuid,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None

    record.status = "available"
    record.size_bytes = size_bytes
    record.sha256 = sha256
    await db.flush()
    return {
        "file_id": str(record.id),
        "purpose": record.purpose,
        "status": record.status,
    }


async def get_access_url(
    db: AsyncSession,
    child_id: str,
    file_id: str,
) -> dict | None:
    """Get file access URL for a car device.

    Validates the child can access this file via child→parent binding.
    """
    parent_uuid = await _get_parent_id_for_child(db, child_id)
    if parent_uuid is None:
        return None

    try:
        fid = uuid.UUID(file_id)
    except ValueError:
        return None

    result = await db.execute(
        select(FileUpload).where(
            FileUpload.id == fid,
            FileUpload.parent_id == parent_uuid,
        )
    )
    record = result.scalar_one_or_none()
    if record is None or record.status != "available":
        return None

    expires_at = datetime.now(SHANGHAI_TZ) + timedelta(hours=1)
    url = f"/uploads/{record.storage_path}"
    return {"file_id": str(record.id), "url": url, "expires_at": expires_at}
