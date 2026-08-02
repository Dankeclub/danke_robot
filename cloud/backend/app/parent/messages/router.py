"""Parent messages routes — list, create, delete."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.messages.schemas import (
    MessageOut,
    PaginatedMessages,
    SendMessageRequest,
)
from app.parent.messages.service import create_message, delete_message, get_messages
from app.schemas.common import error, ok

messages_router = APIRouter(prefix="/children", tags=["parent-messages"])


@messages_router.get("/{child_id}/messages")
async def list_messages(
    child_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_messages(db, parent_id, child_id, page, page_size)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(PaginatedMessages(
        items=[MessageOut(**item) for item in data["items"]],
        pagination=data["pagination"],
    ).model_dump())


@messages_router.post("/{child_id}/messages")
async def send_message(
    child_id: str,
    body: SendMessageRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_message(db, parent_id, child_id, body.type, body.content)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if item is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(MessageOut(**item).model_dump())


@messages_router.delete("/{child_id}/messages/{message_id}")
async def delete_message_endpoint(
    child_id: str,
    message_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        found = await delete_message(db, parent_id, child_id, message_id)
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if not found:
        return JSONResponse(status_code=404, content=error(404, "message_not_found"))
    return ok()
