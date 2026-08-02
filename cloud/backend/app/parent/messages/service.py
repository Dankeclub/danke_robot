"""Parent messages business logic."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ParentMessage
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def get_messages(
    db: AsyncSession, parent_id: str, child_id: str,
    page: int = 1, page_size: int = 20,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    query = (
        select(ParentMessage)
        .where(
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
            ParentMessage.is_deleted == False,  # noqa: E712
        )
        .order_by(ParentMessage.created_at.desc())
    )
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    msgs = result.scalars().all()

    items = []
    for m in msgs:
        reply_result = await db.execute(
            select(ParentMessage)
            .where(
                ParentMessage.replied_to_id == m.id,
                ParentMessage.is_deleted == False,  # noqa: E712
            )
            .order_by(ParentMessage.created_at)
        )
        replies = [
            {
                "reply_id": str(r.id), "type": r.msg_type,
                "preset_code": (
                    r.content.get("preset_code")
                    if isinstance(r.content, dict) else None
                ),
                "text": (
                    r.content.get("text")
                    if isinstance(r.content, dict) else None
                ),
                "created_at": r.created_at,
            }
            for r in reply_result.scalars().all()
        ]
        items.append({
            "message_id": str(m.id),
            "direction": m.direction,
            "type": m.msg_type,
            "content": m.content if isinstance(m.content, dict) else {},
            "created_at": m.created_at,
            "replies": replies,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "items": items,
        "pagination": {
            "page": page, "page_size": page_size,
            "total": total, "total_pages": total_pages,
        },
    }


async def create_message(
    db: AsyncSession, parent_id: str, child_id: str,
    msg_type: str, content: dict,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    msg = ParentMessage(
        child_id=child_id, parent_id=parent_id,
        direction="parent_to_child",
        msg_type=msg_type, content=content,
    )
    db.add(msg)
    await db.flush()
    return {
        "message_id": str(msg.id),
        "direction": msg.direction,
        "type": msg.msg_type,
        "content": content,
        "created_at": msg.created_at,
        "replies": [],
    }


async def delete_message(
    db: AsyncSession, parent_id: str, child_id: str, message_id: str,
) -> bool:
    if not await verify_parent_access(db, parent_id, child_id):
        return False
    try:
        mid = uuid.UUID(message_id)
    except ValueError:
        return False
    result = await db.execute(
        select(ParentMessage).where(
            ParentMessage.id == mid,
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
        )
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        return False
    msg.is_deleted = True
    await db.flush()
    return True
