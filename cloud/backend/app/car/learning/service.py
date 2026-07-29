"""Car learning business logic — park, sessions, batches, content selection."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.car.learning.schemas import (
    category_label,
    difficulty_label,
    module_label,
)
from app.models.config import LearningModuleConfig
from app.models.content import (
    EnglishWord,
    MathQuestion,
    MusicTrack,
    PoemContent,
    QuizQuestion,
    ScienceArticle,
)
from app.models.learning import BatchItem, LearningBatch, LearningSession

_MODULES = ["science", "math", "english", "poems", "music", "quiz"]

_CONTENT_TABLES = {
    "science": ScienceArticle,
    "math": MathQuestion,
    "english": EnglishWord,
    "poems": PoemContent,
    "music": MusicTrack,
    "quiz": QuizQuestion,
}


async def get_learning_park(
    db: AsyncSession, child_id: str
) -> list[dict]:
    """Build learning park: current configs + active sessions for a child."""
    child_uuid = uuid.UUID(child_id)

    # Fetch configs
    result = await db.execute(
        select(LearningModuleConfig).where(
            LearningModuleConfig.child_id == child_uuid,
        )
    )
    configs = {c.module: c for c in result.scalars().all()}

    # Fetch active sessions
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.child_id == child_uuid,
            LearningSession.status == "active",
        )
    )
    active_sessions = {s.module: s for s in result.scalars().all()}

    modules = []
    for mod in _MODULES:
        cfg = configs.get(mod)
        sess = active_sessions.get(mod)

        if cfg is None:
            # Create default config if missing
            cfg = LearningModuleConfig(
                child_id=child_uuid,
                module=mod,
                enabled=True,
                batch_size=_default_batch_size(mod),
                difficulty=_default_difficulty(mod),
                category=_default_category(mod),
            )
            db.add(cfg)
            await db.flush()

        modules.append({
            "module": mod,
            "module_label": module_label(mod),
            "enabled_for_today_task": cfg.enabled,
            "difficulty": cfg.difficulty,
            "difficulty_label": difficulty_label(mod, cfg.difficulty),
            "category": cfg.category,
            "category_label": category_label(cfg.category),
            "batch_size": cfg.batch_size,
            "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
            "config_version": cfg.config_version,
            "active_session_id": str(sess.id) if sess else None,
        })

    return modules


async def create_session(
    db: AsyncSession,
    child_id: str,
    module: str,
    source: str,
    task_id: str | None = None,
    navigation_id: str | None = None,
) -> dict:
    """Create or resume a learning session."""
    child_uuid = uuid.UUID(child_id)

    # Check for existing active session
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.child_id == child_uuid,
            LearningSession.module == module,
            LearningSession.status == "active",
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return _session_to_dict(existing)

    # Fetch current config for snapshot
    result = await db.execute(
        select(LearningModuleConfig).where(
            LearningModuleConfig.child_id == child_uuid,
            LearningModuleConfig.module == module,
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = LearningModuleConfig(
            child_id=child_uuid,
            module=module,
            batch_size=_default_batch_size(module),
            difficulty=_default_difficulty(module),
            category=_default_category(module),
        )
        db.add(cfg)
        await db.flush()

    config_snapshot = {
        "difficulty": cfg.difficulty,
        "difficulty_label": difficulty_label(module, cfg.difficulty),
        "category": cfg.category,
        "category_label": category_label(cfg.category),
        "batch_size": cfg.batch_size,
        "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
        "config_version": cfg.config_version,
    }

    session = LearningSession(
        child_id=child_uuid,
        module=module,
        source=source,
        task_id=task_id,
        navigation_id=navigation_id,
        status="active",
        config_snapshot=config_snapshot,
    )
    db.add(session)
    await db.flush()
    return _session_to_dict(session)


async def create_batch(
    db: AsyncSession,
    child_id: str,
    module: str,
    session_id: str,
) -> dict:
    """Select content items and create an immutable batch."""
    session_uuid = uuid.UUID(session_id)

    # Verify session exists and is active
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_uuid,
            LearningSession.status == "active",
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError("session_not_found")

    # Check for existing batch (same sequence)
    result = await db.execute(
        select(LearningBatch).where(
            LearningBatch.session_id == session_uuid,
        ).order_by(LearningBatch.sequence_no.desc()).limit(1)
    )
    latest_batch = result.scalar_one_or_none()

    sequence_no = (latest_batch.sequence_no + 1) if latest_batch else 1

    # If a batch already exists at this sequence, return it (idempotent)
    if latest_batch and latest_batch.sequence_no == sequence_no:
        result = await db.execute(
            select(BatchItem).where(
                BatchItem.batch_id == latest_batch.id,
            ).order_by(BatchItem.item_order)
        )
        items = result.scalars().all()
        return _batch_to_dict(latest_batch, items, session)

    config = session.config_snapshot or {}
    batch_size = config.get("batch_size", 10)
    difficulty = config.get("difficulty")
    category = config.get("category")

    # Select content items
    content_table = _CONTENT_TABLES[module]
    query = select(content_table).where(content_table.status == "published")

    if module == "music":
        if category:
            query = query.where(content_table.category == category)  # type: ignore[attr-defined]
    else:
        if difficulty:
            query = query.where(content_table.difficulty == difficulty)  # type: ignore[attr-defined]

    query = query.order_by(content_table.created_at).limit(batch_size)  # type: ignore[attr-defined]
    result = await db.execute(query)
    content_items = result.scalars().all()

    if len(content_items) < batch_size:
        raise ValueError("content_pool_exhausted")

    # Create batch
    batch = LearningBatch(
        session_id=session_uuid,
        module=module,
        sequence_no=sequence_no,
        config_snapshot=config,
        issued_at=datetime.now(UTC),
        status="active",
    )
    db.add(batch)
    await db.flush()

    # Create batch items with content snapshots
    batch_items = []
    for i, item in enumerate(content_items):
        # Build content snapshot — flatten model columns to dict
        snapshot = {}
        for col in item.__table__.columns:
            val = getattr(item, col.key)
            if isinstance(val, uuid.UUID):
                val = str(val)
            elif isinstance(val, datetime):
                val = val.isoformat()
            snapshot[col.key] = val

        bi = BatchItem(
            batch_id=batch.id,
            content_id=str(item.id),
            content_type=content_table.__tablename__,
            content_snapshot=snapshot,
            item_order=i,
        )
        batch_items.append(bi)
        db.add(bi)

    await db.flush()
    return _batch_to_dict(batch, batch_items, session)


def _session_to_dict(s: LearningSession) -> dict:
    return {
        "session_id": str(s.id),
        "module": s.module,
        "source": s.source,
        "task_id": s.task_id,
        "status": s.status,
        "config_snapshot": s.config_snapshot or {},
    }


def _batch_to_dict(
    batch: LearningBatch, items: list[BatchItem], session: LearningSession
) -> dict:
    config = session.config_snapshot or {}
    return {
        "batch_id": str(batch.id),
        "session_id": str(session.id),
        "module": batch.module,
        "difficulty": config.get("difficulty"),
        "difficulty_label": config.get("difficulty_label"),
        "category": config.get("category"),
        "category_label": config.get("category_label"),
        "config_snapshot": config,
        "items": [
            {
                "item_order": bi.item_order,
                "content_id": bi.content_id,
                "content_snapshot": bi.content_snapshot,
            }
            for bi in items
        ],
    }


def _default_batch_size(module: str) -> int:
    defaults = {"science": 3, "math": 10, "english": 8, "poems": 2, "music": 5, "quiz": 10}
    return defaults.get(module, 10)


def _default_difficulty(module: str) -> str | None:
    if module == "music":
        return None
    defaults = {
        "science": "beginner", "math": "within_10_add_subtract",
        "english": "grade_3", "poems": "enlightenment", "quiz": "beginner",
    }
    return defaults.get(module)


def _default_category(module: str) -> str | None:
    return "children_song" if module == "music" else None
