"""Seed learning config and content data for development.

Usage:
    cd cloud/backend
    python scripts/seed_learning_data.py

The script creates default LearningModuleConfig rows for a given child and
inserts sample content items for all six learning modules.

The child and family must already exist. Either use an existing child_id or
let the script find the first child in the database.
"""

# ruff: noqa: E501 (inline Chinese text data)
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import async_engine
from app.models.child import Child
from app.models.config import LearningModuleConfig
from app.models.content import (
    EnglishWord,
    MathQuestion,
    MusicTrack,
    PoemContent,
    QuizQuestion,
    ScienceArticle,
)

# ── Default configs per module ────────────────────────────────

DEFAULT_CONFIGS = [
    {"module": "science", "difficulty": "beginner", "category": None, "batch_size": 3},
    {"module": "math", "difficulty": "within_10_add_subtract", "category": None, "batch_size": 10},
    {"module": "english", "difficulty": "grade_3", "category": None, "batch_size": 8},
    {"module": "poems", "difficulty": "enlightenment", "category": None, "batch_size": 2},
    {"module": "music", "difficulty": None, "category": "children_song", "batch_size": 5},
    {"module": "quiz", "difficulty": "beginner", "category": None, "batch_size": 10},
]


async def seed_configs(session: AsyncSession, child_id: uuid.UUID) -> None:
    """Create default LearningModuleConfig for all 6 modules."""
    for cfg in DEFAULT_CONFIGS:
        existing = await session.execute(
            select(LearningModuleConfig).where(
                LearningModuleConfig.child_id == child_id,
                LearningModuleConfig.module == cfg["module"],
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        session.add(LearningModuleConfig(
            child_id=child_id,
            module=cfg["module"],
            difficulty=cfg["difficulty"],
            category=cfg["category"],
            batch_size=cfg["batch_size"],
            enabled=True,
            config_version=1,
        ))
    await session.flush()
    print(f"  Configs seeded for child {child_id}")


# ── Science ───────────────────────────────────────────────────

SCIENCE_ARTICLES = [
    {"difficulty": "beginner", "title": "为什么天空是蓝色的？", "content": "太阳光中有七种颜色...（省略正文）当阳光穿过大气层时，蓝光被散射得最多，所以我们看到的天空是蓝色的。"},
    {"difficulty": "beginner", "title": "蝴蝶是怎么变出来的？", "content": "蝴蝶的一生要经历四个阶段：卵、幼虫、蛹、成虫。毛毛虫就是蝴蝶的幼虫..."},
    {"difficulty": "beginner", "title": "为什么人会做梦？", "content": "当我们睡着的时候，大脑并没有完全休息。它会把白天学到的东西整理一遍..."},
    {"difficulty": "intermediate", "title": "恐龙是怎么灭绝的？", "content": "大约6600万年前，一颗巨大的小行星撞击了地球..."},
    {"difficulty": "intermediate", "title": "水循环的秘密", "content": "地球上的水一直在循环：从海洋蒸发→形成云→降雨→流入河流→回到海洋..."},
]

# ── Math ──────────────────────────────────────────────────────

MATH_QUESTIONS = [
    {"difficulty": "within_10_add_subtract", "question": "3 + 4 = ?", "option_a": "6", "option_b": "7", "option_c": "8", "option_d": "9", "correct_option_id": "B"},
    {"difficulty": "within_10_add_subtract", "question": "8 - 3 = ?", "option_a": "4", "option_b": "6", "option_c": "5", "option_d": "7", "correct_option_id": "C"},
    {"difficulty": "within_10_add_subtract", "question": "2 + 5 = ?", "option_a": "7", "option_b": "6", "option_c": "8", "option_d": "9", "correct_option_id": "A"},
    {"difficulty": "within_10_add_subtract", "question": "9 - 6 = ?", "option_a": "2", "option_b": "3", "option_c": "4", "option_d": "5", "correct_option_id": "B"},
    {"difficulty": "within_10_add_subtract", "question": "1 + 8 = ?", "option_a": "8", "option_b": "7", "option_c": "9", "option_d": "10", "correct_option_id": "C"},
    {"difficulty": "within_10_multiply_divide", "question": "2 × 3 = ?", "option_a": "5", "option_b": "6", "option_c": "8", "option_d": "9", "correct_option_id": "B"},
    {"difficulty": "within_10_multiply_divide", "question": "8 ÷ 2 = ?", "option_a": "3", "option_b": "5", "option_c": "4", "option_d": "6", "correct_option_id": "C"},
    {"difficulty": "within_10_multiply_divide", "question": "5 × 2 = ?", "option_a": "7", "option_b": "8", "option_c": "9", "option_d": "10", "correct_option_id": "D"},
]

# ── English ───────────────────────────────────────────────────

ENGLISH_WORDS = [
    {"difficulty": "grade_3", "chinese": "苹果", "english": "apple", "phonetic": "/ˈæp.əl/", "example_sentence": "I ate an apple for breakfast."},
    {"difficulty": "grade_3", "chinese": "猫", "english": "cat", "phonetic": "/kæt/", "example_sentence": "The cat is sleeping on the sofa."},
    {"difficulty": "grade_3", "chinese": "狗", "english": "dog", "phonetic": "/dɒɡ/", "example_sentence": "My dog loves to run in the park."},
    {"difficulty": "grade_3", "chinese": "书", "english": "book", "phonetic": "/bʊk/", "example_sentence": "I am reading a very interesting book."},
    {"difficulty": "grade_3", "chinese": "水", "english": "water", "phonetic": "/ˈwɔː.tər/", "example_sentence": "Please give me a glass of water."},
    {"difficulty": "grade_4", "chinese": "美丽的", "english": "beautiful", "phonetic": "/ˈbjuː.tɪ.fəl/", "example_sentence": "The garden looks beautiful in spring."},
    {"difficulty": "grade_4", "chinese": "勇敢的", "english": "brave", "phonetic": "/breɪv/", "example_sentence": "The brave firefighter saved the family."},
    {"difficulty": "grade_4", "chinese": "美味的", "english": "delicious", "phonetic": "/dɪˈlɪʃ.əs/", "example_sentence": "My mom makes the most delicious cookies."},
]

# ── Poems ─────────────────────────────────────────────────────

POEMS = [
    {"difficulty": "enlightenment", "title": "静夜思", "author": "李白", "dynasty": "唐", "content_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。"},
    {"difficulty": "enlightenment", "title": "咏鹅", "author": "骆宾王", "dynasty": "唐", "content_text": "鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。"},
    {"difficulty": "enlightenment", "title": "春晓", "author": "孟浩然", "dynasty": "唐", "content_text": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。"},
    {"difficulty": "beginner", "title": "登鹳雀楼", "author": "王之涣", "dynasty": "唐", "content_text": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。"},
    {"difficulty": "beginner", "title": "悯农", "author": "李绅", "dynasty": "唐", "content_text": "锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。"},
]

# ── Music ─────────────────────────────────────────────────────

MUSIC_TRACKS = [
    {"category": "children_song", "name": "小星星", "duration_ms": 120000},
    {"category": "children_song", "name": "两只老虎", "duration_ms": 90000},
    {"category": "children_song", "name": "小燕子", "duration_ms": 105000},
    {"category": "children_song", "name": "找朋友", "duration_ms": 85000},
    {"category": "children_song", "name": "数鸭子", "duration_ms": 110000},
    {"category": "popular_music", "name": "阳光总在风雨后", "duration_ms": 240000},
    {"category": "classical_music", "name": "月光奏鸣曲（片段）", "duration_ms": 300000},
]

# ── Quiz ──────────────────────────────────────────────────────

QUIZ_QUESTIONS = [
    {"difficulty": "beginner", "question": "中国的首都是哪个城市？", "option_a": "上海", "option_b": "北京", "option_c": "广州", "option_d": "深圳", "correct_option_id": "B"},
    {"difficulty": "beginner", "question": "一年有多少天？", "option_a": "360天", "option_b": "365天", "option_c": "370天", "option_d": "355天", "correct_option_id": "B"},
    {"difficulty": "beginner", "question": "太阳从哪个方向升起？", "option_a": "西边", "option_b": "北边", "option_c": "东边", "option_d": "南边", "correct_option_id": "C"},
    {"difficulty": "beginner", "question": "哪种动物会飞？", "option_a": "鱼", "option_b": "狗", "option_c": "鸟", "option_d": "猫", "correct_option_id": "C"},
    {"difficulty": "beginner", "question": "7 + 6 等于多少？", "option_a": "12", "option_b": "13", "option_c": "14", "option_d": "15", "correct_option_id": "B"},
    {"difficulty": "intermediate", "question": "世界上最大的海洋是？", "option_a": "大西洋", "option_b": "印度洋", "option_c": "太平洋", "option_d": "北冰洋", "correct_option_id": "C"},
    {"difficulty": "intermediate", "question": "地球绕太阳转一圈需要多长时间？", "option_a": "一天", "option_b": "一个月", "option_c": "一年", "option_d": "十年", "correct_option_id": "C"},
]


async def seed_content(session: AsyncSession) -> None:
    """Insert sample content for all six modules."""

    for item in SCIENCE_ARTICLES:
        session.add(ScienceArticle(**item))
    print(f"  Science: {len(SCIENCE_ARTICLES)} articles")

    for item in MATH_QUESTIONS:
        session.add(MathQuestion(**item))
    print(f"  Math: {len(MATH_QUESTIONS)} questions")

    for item in ENGLISH_WORDS:
        session.add(EnglishWord(**item))
    print(f"  English: {len(ENGLISH_WORDS)} words")

    for item in POEMS:
        session.add(PoemContent(**item))
    print(f"  Poems: {len(POEMS)} poems")

    for item in MUSIC_TRACKS:
        session.add(MusicTrack(**item))
    print(f"  Music: {len(MUSIC_TRACKS)} tracks")

    for item in QUIZ_QUESTIONS:
        session.add(QuizQuestion(**item))
    print(f"  Quiz: {len(QUIZ_QUESTIONS)} questions")

    await session.flush()


async def main() -> None:
    """Seed learning data: configs + content."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # Find or create a child for seeding
        from app.models.family import Family

        result = await session.execute(select(Child).limit(1))
        child = result.scalar_one_or_none()

        if child is None:
            family = Family(name="种子家庭")
            session.add(family)
            await session.flush()

            child = Child(family_id=family.id, nickname="测试孩子")
            session.add(child)
            await session.flush()
            print(f"Created child: {child.nickname} ({child.id})")

        print(f"Seeding for child: {child.nickname} ({child.id})")

        await seed_configs(session, child.id)
        await seed_content(session)
        await session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
