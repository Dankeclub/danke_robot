"""Car parent-message routes — list recent messages, send replies."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.car.messages.schemas import (
    MessageReply,
    ParentMessageOut,
    ParentMessagesList,
    SendReplyRequest,
)
from app.car.messages.service import create_reply, get_messages
from app.db import get_db
from app.schemas.common import error, ok

messages_router = APIRouter(prefix="/parent-messages", tags=["car-messages"])


@messages_router.get("")
async def list_messages(
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    child_id = device["child_id"]
    family_id = device.get("family_id", "")
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    # Resolve parent_id from child's default binding via family_id
    from app.models.parent_child import ParentChild
    from sqlalchemy import select

    result = await db.execute(
        select(ParentChild.parent_id).where(
            ParentChild.child_id == child_id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.first()
    if row is None:
        return JSONResponse(status_code=404, content=error(404, "no_parent_binding"))

    parent_id = str(row[0])

    try:
        data = await get_messages(db, child_id, parent_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    items = [ParentMessageOut(
        message_id=item["message_id"],
        type=item["type"],
        content=item["content"],
        created_at=item["created_at"],
        replies=[MessageReply(**r) for r in item["replies"]],
    ) for item in data["items"]]
    return ok(ParentMessagesList(items=items).model_dump())


@messages_router.post("/{message_id}/replies")
async def send_reply(
    message_id: str,
    body: SendReplyRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    child_id = device["child_id"]
    if not child_id:
        return JSONResponse(status_code=400, content=error(400, "missing_child_id"))

    # Resolve parent_id
    from app.models.parent_child import ParentChild
    from sqlalchemy import select

    result = await db.execute(
        select(ParentChild.parent_id).where(
            ParentChild.child_id == child_id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.first()
    if row is None:
        return JSONResponse(status_code=404, content=error(404, "no_parent_binding"))

    parent_id = str(row[0])

    # Validate: preset_text requires preset_code, voice requires file_id
    if body.type == "preset_text" and not body.preset_code:
        return JSONResponse(status_code=400, content=error(400, "missing_preset_code"))
    if body.type == "voice" and not body.file_id:
        return JSONResponse(status_code=400, content=error(400, "missing_file_id"))

    try:
        reply = await create_reply(
            db, child_id, parent_id, message_id,
            body.type, body.preset_code, body.file_id, body.duration_ms,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if reply is None:
        return JSONResponse(status_code=404, content=error(404, "message_not_found"))
    return ok(reply)
