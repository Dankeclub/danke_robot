"""Car file routes — upload init, complete, access."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.car.files.schemas import (
    FileAccessOut,
    UploadCompleteRequest,
    UploadInitOut,
    UploadInitRequest,
)
from app.car.files.service import complete_upload, get_access_url, init_upload
from app.db import get_db
from app.schemas.common import error, ok

files_router = APIRouter(prefix="/files", tags=["car-files"])


@files_router.post("/uploads")
async def initiate_upload(
    body: UploadInitRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        data = await init_upload(
            db, child_id, body.purpose, body.file_name,
            body.content_type, body.size_bytes, body.sha256,
        )
        await db.commit()
    except ValueError:
        await db.rollback()
        return JSONResponse(status_code=400, content=error(400, "no_parent_binding"))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    return ok(UploadInitOut(**data).model_dump())


@files_router.post("/uploads/{upload_id}/complete")
async def confirm_upload(
    upload_id: str,
    body: UploadCompleteRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        data = await complete_upload(
            db, child_id, upload_id, body.size_bytes, body.sha256,
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
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    try:
        data = await get_access_url(db, child_id, file_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "file_not_found"))
    return ok(FileAccessOut(**data).model_dump())
