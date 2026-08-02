"""Parent file routes — upload init, complete, access."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.files.schemas import (
    FileAccessOut,
    UploadCompleteRequest,
    UploadInitOut,
    UploadInitRequest,
)
from app.parent.files.service import complete_upload, get_access_url, init_upload
from app.schemas.common import error, ok

files_router = APIRouter(prefix="/files", tags=["parent-files"])


@files_router.post("/uploads")
async def initiate_upload(
    body: UploadInitRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await init_upload(
            db, parent_id, body.purpose, body.file_name,
            body.content_type, body.size_bytes, body.sha256,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    return ok(UploadInitOut(**data).model_dump())


@files_router.post("/uploads/{upload_id}/complete")
async def confirm_upload(
    upload_id: str,
    body: UploadCompleteRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await complete_upload(
            db, parent_id, upload_id, body.size_bytes, body.sha256,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "upload_not_found"))
    return ok(data)


@files_router.get("/{file_id}/access")
async def file_access(
    file_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_access_url(db, parent_id, file_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "file_not_found"))
    return ok(FileAccessOut(**data).model_dump())
