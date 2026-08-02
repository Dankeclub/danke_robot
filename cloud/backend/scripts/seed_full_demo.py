"""One-shot full demo data seeder.

Creates a complete demo environment with:
  - 1 parent, 1 family, 1 child, 1 device binding
  - 6 module configs with defaults
  - Learning goal (120 min/day)
  - Content for all 6 modules (poems, math, english, science, music, quiz)
  - 7 days of daily tasks
  - 5 completed learning sessions with answer records
  - 14 days of behavior events (focus, posture, location)

Prerequisites: PostgreSQL must be running and alembic migrations applied.
  cd cloud/backend
  alembic upgrade head          # <-- run this first
  python scripts/seed_full_demo.py

Idempotent: checks for existing demo parent before seeding.
"""

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import async_engine
from app.models.child import Child
from app.models.device_binding import DeviceBinding
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from scripts.seed_behavior_data import seed_behavior_for_child
from scripts.seed_learning_data import DEFAULT_CONFIGS, seed_content

SHANGHAI_TZ = timezone(timedelta(hours=8))
MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}


async def main() -> None:
    """Run full demo seed."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False,
    )

    # Check tables exist
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_name = 'parent_account'"
                    ")"
                )
            )
            tables_exist = result.scalar()
    except Exception:
        tables_exist = False

    if not tables_exist:
        print("=" * 60)
        print("ERROR: Database tables not found.")
        print("Run this command first, then re-run this script:")
        print()
        print("  cd cloud/backend && alembic upgrade head")
        print()
        print("(PostgreSQL must be running — check 'docker compose ps db')")
        print("=" * 60)
        return

    async with session_factory() as session:
        # 1. Check if already seeded
        existing = await session.execute(
            select(ParentAccount).where(
                ParentAccount.wx_openid == "demo_parent_seed",
            ),
        )
        if existing.scalar_one_or_none():
            print("Demo data already exists, skipping.")
            return

        # 2. Create demo parent
        parent = ParentAccount(
            wx_openid="demo_parent_seed",
            nickname="演示家长",
            status="active",
            phone_masked="138****0000",
        )
        session.add(parent)
        await session.flush()
        print(f"Created parent: {parent.id}")

        # 3. Create family
        family = Family(name="演示家庭")
        session.add(family)
        await session.flush()

        # 4. Create child
        child = Child(
            family_id=family.id, nickname="小宇",
            birth_date=date(2019, 6, 1), gender="boy",
        )
        session.add(child)
        await session.flush()

        # 5. Parent-child binding
        session.add(ParentChild(
            parent_id=parent.id, child_id=child.id,
            family_id=family.id, status="active", is_default=True,
        ))

        # 6. Device binding
        session.add(DeviceBinding(
            device_id="demo_car_001", child_id=child.id,
            device_name="小宇的车机", device_type="car", bind_status="active",
        ))
        await session.flush()
        print(f"Created child: {child.nickname} ({child.id})")

        # 7. Seed configs and content (from existing seed script)
        from app.models.config import LearningModuleConfig
        for cfg in DEFAULT_CONFIGS:
            session.add(LearningModuleConfig(
                child_id=child.id, module=cfg["module"],
                difficulty=cfg.get("difficulty"),
                category=cfg.get("category"),
                batch_size=cfg["batch_size"],
                enabled=True, config_version=1,
            ))
        print("  Configs seeded")
        await seed_content(session)

        # 8. Seed learning goal
        from app.models.config import LearningGoal
        session.add(LearningGoal(
            child_id=child.id, daily_goal_minutes=120,
            module_goals=[
                {"module": mod, "goal_minutes": goal_min}
                for mod, goal_min in [
                    ("math", 30), ("science", 20), ("english", 20),
                    ("poems", 20), ("music", 15), ("quiz", 15),
                ]
            ],
        ))

        # 9. Create 7 days of daily tasks
        from app.models.task import DailyTask
        today = date.today()
        modules = ["math", "science", "english", "poems", "music", "quiz"]
        for days_ago in range(7):
            d = today - timedelta(days=days_ago)
            for mod in modules:
                expires = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=SHANGHAI_TZ)
                status = "completed" if days_ago > 0 else random.choice(
                    ["completed", "in_progress", "assigned"],
                )
                session.add(DailyTask(
                    child_id=child.id, business_date=d, module=mod,
                    task_category="learning",
                    title=f"今日{MODULE_LABELS[mod]}",
                    status=status,
                    progress_completed=(
                        random.randint(5, 10) if status == "completed" else 0
                    ),
                    progress_total=10, expires_at=expires,
                ))
        await session.flush()
        print("  Tasks seeded (7 days × 6 modules)")

        # 10. Create learning sessions with batches and answers
        from app.models.answer import AnswerRecord
        from app.models.learning import BatchItem, LearningBatch, LearningSession
        for days_ago in [1, 2, 3, 4, 5]:
            d = today - timedelta(days=days_ago)
            for mod in random.sample(modules, 3):
                st = datetime(
                    d.year, d.month, d.day,
                    random.randint(9, 17), 0, 0, tzinfo=SHANGHAI_TZ,
                )
                session_obj = LearningSession(
                    child_id=child.id, module=mod,
                    source="today_task", status="completed",
                )
                session.add(session_obj)
                await session.flush()

                # Create a batch + items for the session (required by answer FK)
                batch = LearningBatch(
                    session_id=session_obj.id, module=mod,
                    sequence_no=1,
                )
                session.add(batch)
                await session.flush()

                for _ in range(random.randint(5, 10)):
                    is_correct = random.random() < 0.75
                    # Create batch_item first, then answer referencing it
                    item = BatchItem(
                        batch_id=batch.id,
                        content_id=f"demo_{mod}_{days_ago}_{_}",
                        content_type=mod,
                        content_snapshot={"question": f"Demo question {_}"},
                        item_order=_,
                        created_at=datetime.now(SHANGHAI_TZ),
                    )
                    session.add(item)
                    await session.flush()

                    session.add(AnswerRecord(
                        session_id=session_obj.id,
                        batch_item_id=item.id,
                        child_id=child.id, module=mod,
                        question_snapshot={
                            "question": f"Demo question {_}",
                            "options": [],
                        },
                        selected_option_id="A" if is_correct else "B",
                        correct_option_id="A",
                        is_correct=is_correct,
                        answer_duration_ms=random.randint(2000, 15000),
                        answered_at=st + timedelta(
                            minutes=random.randint(1, 30),
                        ),
                    ))
        await session.flush()
        print("  Sessions + answers seeded (5 days × 3 modules)")

        # 11. Seed behavior events
        await seed_behavior_for_child(session, child.id)

        await session.commit()
        print("\n=== Full demo seed complete! ===")
        print("Parent demo_openid: demo_parent_seed")
        print(f"Child ID: {child.id}")
        print(f"Family ID: {family.id}")
        print("Device ID: demo_car_001")
        print()
        print("Run the backend: uvicorn app.main:app --reload")
        print("Use the parent JWT with parent_id=" + str(parent.id))


if __name__ == "__main__":
    asyncio.run(main())
