"""Parent file service — Phase 3 local storage, Phase 4 OSS/S3."""

import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def init_upload(
    db: AsyncSession, parent_id: str,
    purpose: str, file_name: str, content_type: str,
    size_bytes: int, sha256: str,
) -> dict:
    """Initiate a file upload. Returns upload_id and local storage path."""
    upload_id = uuid.uuid4()
    ext = os.path.splitext(file_name)[1] or ""
    storage_path = f"{purpose}/{upload_id}{ext}"
    expires_at = datetime.now(SHANGHAI_TZ) + timedelta(hours=1)

    record = FileUpload(
        id=upload_id,
        parent_id=parent_id, purpose=purpose, file_name=file_name,
        content_type=content_type, size_bytes=size_bytes,
        sha256=sha256, storage_path=storage_path,
        status="pending", expires_at=expires_at,
    )
    db.add(record)
    await db.flush()
    return {
        "upload_id": str(upload_id),
        "upload_path": storage_path,
        "expires_at": expires_at,
    }


async def complete_upload(
    db: AsyncSession, parent_id: str, upload_id: str,
    size_bytes: int, sha256: str,
) -> dict | None:
    """Confirm upload completion. Marks file as available."""
    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        return None
    result = await db.execute(
        select(FileUpload).where(
            FileUpload.id == uid,
            FileUpload.parent_id == parent_id,
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
    db: AsyncSession, parent_id: str, file_id: str,
) -> dict | None:
    """Get file access URL. Local path for dev, presigned URL for prod."""
    try:
        fid = uuid.UUID(file_id)
    except ValueError:
        return None
    result = await db.execute(
        select(FileUpload).where(
            FileUpload.id == fid,
            FileUpload.parent_id == parent_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None or record.status != "available":
        return None
    expires_at = datetime.now(SHANGHAI_TZ) + timedelta(hours=1)
    url = f"/uploads/{record.storage_path}"
    return {"file_id": str(record.id), "url": url, "expires_at": expires_at}
