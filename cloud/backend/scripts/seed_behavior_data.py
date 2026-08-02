"""Seed behavior events for demo — 14 days of focus/posture/location/zone data.

Usage: cd cloud/backend && python scripts/seed_behavior_data.py

Idempotent: skips children that already have behavior_event rows.
Auto-runs alembic if tables don't exist yet.
"""

import asyncio
import os
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import async_engine
from app.models.behavior import BehaviorEvent
from app.models.child import Child

SHANGHAI_TZ = timezone(timedelta(hours=8))

ZONES = ["客厅", "书房", "卧室"]
MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}
FOCUS_INSIGHTS = [
    {
        "title": "周三下午专注度骤降",
        "description": "15:30-16:20 跌至 62 分，与自由探索时间吻合。中断次数为平时 3.2 倍。",
        "tags": [{"text": "专注度", "cls": "tf"}, {"text": "使用时长", "cls": "tt"}],
    },
    {
        "title": "早上专注度最佳",
        "description": "9:00-11:00 专注度平均 88 分，比下午高 15%。建议将核心学习安排在上午。",
        "tags": [{"text": "专注度", "cls": "tf"}],
    },
]
POSTURE_INSIGHTS = [
    {
        "title": "使用时长 > 90 分钟 → 坐姿问题 +40%",
        "description": "3 天超过 90 分钟，坐姿问题次数平均多出 40%。建议在 80 分钟时触发休息提醒。",
        "tags": [{"text": "坐姿", "cls": "tp"}, {"text": "使用时长", "cls": "tt"}],
    },
    {
        "title": "连续 3 天坐姿改善",
        "description": "本周坐姿评分持续上升，提醒次数减少 60%。继续保持桌面高度和座椅调整。",
        "tags": [{"text": "坐姿", "cls": "tp"}],
    },
]


async def seed_behavior_for_child(
    session: AsyncSession, child_id: uuid.UUID,
) -> None:
    """Generate 14 days of behavior events for one child."""
    today = date.today()
    for days_ago in range(14):
        d = today - timedelta(days=days_ago)
        dt = datetime(d.year, d.month, d.day, tzinfo=SHANGHAI_TZ)

        # 8 focus events per day (roughly one per hour during learning hours)
        for hour in [9, 10, 11, 14, 15, 16, 17, 19]:
            event_time = dt.replace(hour=hour, minute=random.randint(0, 59))
            base_score = 85 + random.randint(-10, 10)
            if d.weekday() in (5, 6):
                base_score -= random.randint(5, 15)
            is_distracted = random.random() < 0.15
            is_interrupted = random.random() < 0.10
            payload = {
                "focus_duration_seconds": random.randint(60, 1800),
                "is_distracted": is_distracted,
                "interrupted": is_interrupted,
                "activity": random.choice(list(MODULE_LABELS)),
            }
            if days_ago == 3 and hour == 15 and random.random() < 0.7:
                payload["insight"] = FOCUS_INSIGHTS[0]
                payload["is_anomaly"] = True
                payload["title"] = FOCUS_INSIGHTS[0]["title"]
                payload["description"] = FOCUS_INSIGHTS[0]["description"]
                payload["tags"] = FOCUS_INSIGHTS[0]["tags"]
            if days_ago == 7 and hour == 9 and random.random() < 0.7:
                payload["insight"] = FOCUS_INSIGHTS[1]
                payload["is_discovery"] = True
                payload["title"] = FOCUS_INSIGHTS[1]["title"]
                payload["description"] = FOCUS_INSIGHTS[1]["description"]
                payload["color"] = "#f9b370"

            session.add(BehaviorEvent(
                child_id=child_id, event_type="focus",
                score=max(0, min(100, base_score)),
                payload=payload, recorded_at=event_time,
            ))

        # 3-5 posture events per day
        for _ in range(random.randint(3, 5)):
            event_time = dt.replace(
                hour=random.randint(8, 20), minute=random.randint(0, 59),
            )
            posture_label = random.choices(
                ["good", "slight_tilt", "obvious_slant"], weights=[7, 2, 1],
            )[0]
            score_map = {"good": 85, "slight_tilt": 60, "obvious_slant": 35}
            payload = {
                "posture_label": posture_label,
                "reminder_sent": posture_label != "good",
            }
            if days_ago == 2 and posture_label == "obvious_slant" and random.random() < 0.7:
                payload["insight"] = POSTURE_INSIGHTS[0]
                payload["is_discovery"] = True
                payload["title"] = POSTURE_INSIGHTS[0]["title"]
                payload["description"] = POSTURE_INSIGHTS[0]["description"]
                payload["color"] = "#778ccd"
            session.add(BehaviorEvent(
                child_id=child_id, event_type="posture",
                score=max(0, min(100, score_map[posture_label] + random.randint(-5, 5))),
                payload=payload, recorded_at=event_time,
            ))

        # 1-2 zone/location events per day
        zone = random.choice(ZONES)
        for _ in range(random.randint(1, 2)):
            event_time = dt.replace(
                hour=random.randint(8, 20), minute=random.randint(0, 59),
            )
            session.add(BehaviorEvent(
                child_id=child_id, event_type="location",
                score=100, payload={"zone_name": zone, "zone_change": False},
                recorded_at=event_time,
            ))

    await session.flush()
    print(f"  Behavior events seeded for child {child_id}")


async def main() -> None:
    """Seed behavior events for all existing children. Auto-runs alembic if needed."""
    # Check if tables exist; run alembic if not
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_name = 'behavior_event'"
                    ")"
                )
            )
            tables_exist = result.scalar()
    except Exception:
        tables_exist = False

    if not tables_exist:
        print("Tables not found — running alembic upgrade head...")
        from alembic import command
        from alembic.config import Config as AlembicConfig

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = AlembicConfig(os.path.join(backend_dir, "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        print("Migration complete.\n")

    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with session_factory() as session:
        result = await session.execute(select(Child).limit(10))
        children = result.scalars().all()

        if not children:
            from app.models.family import Family
            family = Family(name="种子家庭-行为")
            session.add(family)
            await session.flush()
            child = Child(family_id=family.id, nickname="测试孩子")
            session.add(child)
            await session.flush()
            children = [child]
            print(f"Created child: {child.nickname} ({child.id})")

        for child in children:
            existing = await session.execute(
                select(BehaviorEvent)
                .where(BehaviorEvent.child_id == child.id)
                .limit(1),
            )
            if existing.scalar_one_or_none():
                print(f"  Child {child.id} already has behavior data, skipping")
                continue
            await seed_behavior_for_child(session, child.id)

        await session.commit()
        print("Seed behavior data complete.")


if __name__ == "__main__":
    asyncio.run(main())
