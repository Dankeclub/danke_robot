"""Car parent-messages business logic — list recent messages, send replies."""

import uuid
from datetime import timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ParentMessage

SHANGHAI_TZ = timezone(timedelta(hours=8))

PRESET_REPLIES = {
    "got_it": "知道了",
    "will_do_now": "马上去做",
    "done": "已经完成啦",
    "later": "等一下去做",
    "thank_you": "谢谢爸爸妈妈",
}

MESSAGE_LIST_LIMIT = 50


async def get_messages(
    db: AsyncSession,
    child_id: str,
    parent_id: str,
) -> dict:
    """Return the most recent parent→child messages and their child replies."""
    query = (
        select(ParentMessage)
        .where(
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
            ParentMessage.direction == "parent_to_child",
            ParentMessage.is_deleted == False,  # noqa: E712
        )
        .order_by(ParentMessage.created_at.desc())
        .limit(MESSAGE_LIST_LIMIT)
    )
    result = await db.execute(query)
    msgs = result.scalars().all()

    # Fetch replies for each message (child→parent, linked via replied_to_id)
    items = []
    for m in reversed(msgs):  # chronological order
        reply_result = await db.execute(
            select(ParentMessage)
            .where(
                ParentMessage.replied_to_id == m.id,
                ParentMessage.is_deleted == False,  # noqa: E712
            )
            .order_by(ParentMessage.created_at)
        )
        replies = [
            _format_reply(r)
            for r in reply_result.scalars().all()
        ]
        items.append({
            "message_id": str(m.id),
            "type": m.msg_type,
            "content": m.content if isinstance(m.content, dict) else {},
            "created_at": m.created_at,
            "replies": replies,
        })

    return {"items": items}


def _format_reply(msg) -> dict:
    """Format a child→parent reply message for the API response."""
    content = msg.content if isinstance(msg.content, dict) else {}
    reply = {
        "reply_id": str(msg.id),
        "type": msg.msg_type,
        "created_at": msg.created_at,
    }
    if msg.msg_type == "preset_text":
        reply["preset_code"] = content.get("preset_code")
        reply["text"] = content.get("text")
    elif msg.msg_type == "voice":
        reply["file_id"] = content.get("file_id")
        reply["duration_ms"] = content.get("duration_ms")
    return reply


async def create_reply(
    db: AsyncSession,
    child_id: str,
    parent_id: str,
    message_id: str,
    reply_type: str,
    preset_code: str | None = None,
    file_id: str | None = None,
    duration_ms: int | None = None,
) -> dict | None:
    """Create a child→parent reply to a parent message.

    reply_type: preset_text | voice
    - preset_text: uses preset_code → looks up Chinese text
    - voice: references a file_id uploaded via the file service
    """
    try:
        mid = uuid.UUID(message_id)
    except ValueError:
        return None

    # Verify the parent message exists and belongs to this child+parent
    result = await db.execute(
        select(ParentMessage).where(
            ParentMessage.id == mid,
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
            ParentMessage.direction == "parent_to_child",
            ParentMessage.is_deleted == False,  # noqa: E712
        )
    )
    parent_msg = result.scalar_one_or_none()
    if parent_msg is None:
        return None

    if reply_type == "preset_text":
        if preset_code not in PRESET_REPLIES:
            return None
        content = {
            "preset_code": preset_code,
            "text": PRESET_REPLIES[preset_code],
        }
    elif reply_type == "voice":
        content = {
            "file_id": file_id or "",
            "duration_ms": duration_ms or 0,
        }
    else:
        return None

    reply = ParentMessage(
        child_id=uuid.UUID(child_id),
        parent_id=uuid.UUID(parent_id),
        direction="child_to_parent",
        msg_type=reply_type,
        content=content,
        replied_to_id=mid,
    )
    db.add(reply)
    await db.flush()

    result = {
        "reply_id": str(reply.id),
        "message_id": message_id,
        "type": reply_type,
        "created_at": reply.created_at,
    }
    if reply_type == "preset_text":
        result["preset_code"] = preset_code
        result["text"] = PRESET_REPLIES[preset_code]
    elif reply_type == "voice":
        result["file_id"] = file_id
        result["duration_ms"] = duration_ms
    return result
