"""Parent learning config business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import ConfigAudit, LearningModuleConfig
from app.parent.service import verify_parent_access

MODULES = ["science", "math", "english", "poems", "music", "quiz"]
MODULE_LABELS = {
    "science": "科学探秘",
    "math": "数学思维",
    "english": "英语角",
    "poems": "诗词歌赋",
    "music": "音乐乐园",
    "quiz": "趣味问答",
}


async def get_learning_config(
    db: AsyncSession, parent_id: str, child_id: str,
) -> list[dict] | None:
    """Get all 6 module configs for a child."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    result = await db.execute(
        select(LearningModuleConfig)
        .where(LearningModuleConfig.child_id == child_id)
        .order_by(LearningModuleConfig.module)
    )
    configs = result.scalars().all()

    modules = []
    for cfg in configs:
        modules.append({
            "module": cfg.module,
            "module_label": MODULE_LABELS.get(cfg.module, cfg.module),
            "enabled": cfg.enabled,
            "effective_config": {
                "difficulty": cfg.difficulty,
                "difficulty_label": _format_label(cfg.difficulty),
                "category": cfg.category,
                "category_label": _format_label(cfg.category),
                "batch_size": cfg.batch_size,
                "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
                "config_version": cfg.config_version,
            },
        })
    return modules


async def update_learning_config(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    modules: list[dict],
) -> list[dict] | None:
    """Bulk update learning module configs. Returns updated config list.

    Raises ValueError if a module name is not recognized.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    updated = []
    for mod_data in modules:
        module = mod_data["module"]
        result = await db.execute(
            select(LearningModuleConfig).where(
                LearningModuleConfig.child_id == child_id,
                LearningModuleConfig.module == module,
            )
        )
        cfg = result.scalar_one_or_none()
        if cfg is None:
            raise ValueError(f"module_not_found: {module}")

        old_values = {
            "enabled": cfg.enabled,
            "difficulty": cfg.difficulty,
            "category": cfg.category,
            "batch_size": cfg.batch_size,
            "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
            "config_version": cfg.config_version,
        }

        # Apply updates
        if "enabled" in mod_data and mod_data["enabled"] is not None:
            cfg.enabled = mod_data["enabled"]
        if "difficulty" in mod_data and mod_data["difficulty"] is not None:
            cfg.difficulty = mod_data["difficulty"]
        if "category" in mod_data and mod_data["category"] is not None:
            cfg.category = mod_data["category"]
        if "batch_size" in mod_data and mod_data["batch_size"] is not None:
            cfg.batch_size = mod_data["batch_size"]
        if (
            "min_repeat_interval_seconds" in mod_data
            and mod_data["min_repeat_interval_seconds"] is not None
        ):
            cfg.min_repeat_interval_seconds = mod_data["min_repeat_interval_seconds"]

        cfg.config_version += 1
        new_version = cfg.config_version

        new_values = {
            "enabled": cfg.enabled,
            "difficulty": cfg.difficulty,
            "category": cfg.category,
            "batch_size": cfg.batch_size,
            "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
            "config_version": new_version,
        }

        # Insert audit record
        audit = ConfigAudit(
            child_id=child_id,
            module=module,
            changed_by=parent_id,
            old_values=old_values,
            new_values=new_values,
        )
        db.add(audit)

        updated.append({
            "module": cfg.module,
            "module_label": MODULE_LABELS.get(cfg.module, cfg.module),
            "enabled": cfg.enabled,
            "effective_config": {
                "difficulty": cfg.difficulty,
                "difficulty_label": _format_label(cfg.difficulty),
                "category": cfg.category,
                "category_label": _format_label(cfg.category),
                "batch_size": cfg.batch_size,
                "min_repeat_interval_seconds": cfg.min_repeat_interval_seconds,
                "config_version": new_version,
            },
        })

    return updated


async def get_config_audit(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    module: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict | None:
    """Get config change audit history with cursor-based pagination."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    query = (
        select(ConfigAudit)
        .where(ConfigAudit.child_id == child_id)
        .order_by(ConfigAudit.created_at.desc())
    )

    if module:
        query = query.where(ConfigAudit.module == module)

    if cursor:
        query = query.where(ConfigAudit.created_at < cursor)

    query = query.limit(limit + 1)

    result = await db.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    items = rows[:limit]

    return {
        "items": [
            {
                "audit_id": str(r.id),
                "module": r.module,
                "changed_by": r.changed_by,
                "old_values": r.old_values,
                "new_values": r.new_values,
                "config_version": r.new_values.get("config_version", 0),
                "created_at": r.created_at.isoformat(),
            }
            for r in items
        ],
        "has_more": has_more,
        "next_cursor": items[-1].created_at.isoformat() if has_more and items else None,
    }


def _format_label(value: str | None) -> str | None:
    """Format technical values into display labels."""
    if value is None:
        return None
    labels = {
        "beginner": "初级",
        "intermediate": "中级",
        "advanced": "高级",
        "within_10_add_subtract": "10以内加减法",
        "within_10_multiply_divide": "10以内乘除法",
        "two_digit_add_subtract": "两位数加减法",
        "two_digit_multiply_divide": "两位数乘除法",
        "three_digit_four_operations": "三位数四则运算",
        "mixed_four_operations": "四则运算混合",
        "grade_3": "三年级",
        "grade_4": "四年级",
        "grade_5": "五年级",
        "grade_6": "六年级",
        "enlightenment": "启蒙",
        "children_song": "儿歌",
        "popular_music": "流行音乐",
        "classical_music": "古典音乐",
        "classic_music": "经典老歌",
        "patriotic_music": "爱国歌曲",
        "mixed": "混合",
    }
    return labels.get(value, value)
