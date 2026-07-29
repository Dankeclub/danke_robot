"""Telemetry event ingestion with idempotency and session completion."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord, WrongAnswer
from app.models.learning import BatchItem, LearningBatch, LearningSession
from app.telemetry.models import LearningEvent


async def insert_events(
    db: AsyncSession,
    device_id: str,
    child_id: str,
    events: list[dict],
) -> tuple[int, int]:
    """Insert events with idempotency. Returns (accepted, duplicates).

    Uses PostgreSQL ON CONFLICT DO NOTHING for idempotent inserts.
    Duplicate (device_id, event_id) pairs are silently skipped.
    """
    if not events:
        return 0, 0

    values = [
        {
            "device_id": device_id,
            "child_id": child_id,
            "event_id": e["event_id"],
            "event_type": e["event_type"],
            "module": e.get("module"),
            "timestamp": e["timestamp"],
            "payload": e.get("payload", {}),
        }
        for e in events
    ]

    stmt = (
        pg_insert(LearningEvent)
        .values(values)
        .on_conflict_do_nothing(index_elements=["device_id", "event_id"])
    )
    result = await db.execute(stmt)
    # ON CONFLICT DO NOTHING: rowcount counts only inserted rows
    accepted = result.rowcount or 0
    duplicates = len(events) - accepted
    await db.flush()
    return accepted, duplicates


async def process_answer_events(
    db: AsyncSession,
    child_id: str,
    events: list[dict],
) -> int:
    """Process answer_submitted events: judge, record, track wrong answers.

    Returns the number of answer events processed.
    """
    child_uuid = uuid.UUID(child_id)
    count = 0

    for evt in events:
        if evt.get("event_type") != "answer_submitted":
            continue

        session_id = evt.get("session_id")
        batch_id = evt.get("batch_id")
        question_id = evt.get("question_id")
        selected = evt.get("selected_option_id")
        module = evt.get("module")

        if not all([session_id, batch_id, question_id, selected, module]):
            continue

        # Find batch item for this question to get correct answer
        result = await db.execute(
            select(BatchItem).where(
                BatchItem.batch_id == uuid.UUID(batch_id),
                BatchItem.content_id == question_id,
            )
        )
        batch_item = result.scalar_one_or_none()
        if batch_item is None:
            continue

        snapshot = batch_item.content_snapshot or {}
        correct = snapshot.get("correct_option_id", "")
        is_correct = selected == correct
        occurred_at = evt.get("timestamp")
        answer_duration = evt.get("answer_duration_ms")

        # Record answer
        answer = AnswerRecord(
            session_id=uuid.UUID(session_id),
            batch_item_id=batch_item.id,
            child_id=child_uuid,
            module=module,
            question_snapshot=snapshot,
            selected_option_id=selected,
            correct_option_id=correct,
            is_correct=is_correct,
            answer_duration_ms=answer_duration,
            answered_at=occurred_at,
        )
        db.add(answer)
        count += 1

        # Track wrong answers
        if not is_correct:
            await _upsert_wrong_answer(
                db, child_uuid, module, question_id,
                selected, correct, snapshot, occurred_at,
            )

    await db.flush()
    return count


async def _upsert_wrong_answer(
    db: AsyncSession,
    child_uuid: uuid.UUID,
    module: str,
    question_id: str,
    selected: str,
    correct: str,
    snapshot: dict,
    occurred_at,
):
    """Insert or update a wrong answer record."""
    result = await db.execute(
        select(WrongAnswer).where(
            WrongAnswer.child_id == child_uuid,
            WrongAnswer.question_id == question_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.wrong_count += 1
        existing.selected_option_id = selected
        existing.last_wrong_at = occurred_at
    else:
        wa = WrongAnswer(
            child_id=child_uuid,
            module=module,
            question_snapshot=snapshot,
            question_id=question_id,
            selected_option_id=selected,
            correct_option_id=correct,
            wrong_count=1,
            first_wrong_at=occurred_at,
            last_wrong_at=occurred_at,
        )
        db.add(wa)


async def complete_session(
    db: AsyncSession,
    child_id: str,
    session_id: str,
) -> dict:
    """Check if a session is complete and update status if so.

    Completion rules (skeleton phase — simplified):
    - Math/Quiz: all batch items have answers
    - Other modules: session status check only (telemetry events exist)
    """
    child_uuid = uuid.UUID(child_id)
    session_uuid = uuid.UUID(session_id)

    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_uuid,
            LearningSession.child_id == child_uuid,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError("session_not_found")
    if session.status != "active":
        return _session_summary_dict(session)

    # Count batch items for this session
    result = await db.execute(
        select(func.count(BatchItem.id))
        .join(LearningBatch, BatchItem.batch_id == LearningBatch.id)
        .where(LearningBatch.session_id == session_uuid)
    )
    total_items = result.scalar() or 0

    # Count answers
    result = await db.execute(
        select(func.count(AnswerRecord.id)).where(
            AnswerRecord.session_id == session_uuid,
        )
    )
    answer_count = result.scalar() or 0

    is_complete = total_items > 0 and answer_count >= total_items
    if is_complete:
        session.status = "completed"
        await db.flush()

    return _session_summary_dict(session)


async def get_session_summary(
    db: AsyncSession,
    child_id: str,
    session_id: str,
) -> dict:
    """Get summary stats for a session."""
    session_uuid = uuid.UUID(session_id)

    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_uuid,
            LearningSession.child_id == uuid.UUID(child_id),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError("session_not_found")

    return _session_summary_dict(session)


async def _get_session_answer_stats(
    db: AsyncSession, session_uuid: uuid.UUID,
) -> tuple[int, int, int]:
    """Return (total_items, answer_count, correct_count)."""
    result = await db.execute(
        select(func.count(BatchItem.id))
        .join(LearningBatch, BatchItem.batch_id == LearningBatch.id)
        .where(LearningBatch.session_id == session_uuid)
    )
    total = result.scalar() or 0

    result = await db.execute(
        select(func.count(AnswerRecord.id)).where(
            AnswerRecord.session_id == session_uuid,
        )
    )
    answered = result.scalar() or 0

    result = await db.execute(
        select(func.count(AnswerRecord.id)).where(
            AnswerRecord.session_id == session_uuid,
            AnswerRecord.is_correct == True,  # noqa: E712
        )
    )
    correct = result.scalar() or 0

    return total, answered, correct


def _session_summary_dict(session: LearningSession) -> dict:
    return {
        "session_id": str(session.id),
        "module": session.module,
        "status": session.status,
        "summary": {
            "completed_count": 0,
            "total_count": 0,
            "accuracy": None,
            "correct_count": 0,
            "wrong_count": 0,
            "total_active_duration_ms": 0,
            "is_final": session.status in ("completed", "expired"),
        },
    }
