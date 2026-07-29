"""Content tables for the six learning modules."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# ── Common status constraint ──────────────────────────────

_content_status_ck = CheckConstraint(
    "status IN ('draft','published','archived')",
    name="ck_content_status",
)


# ── Science ────────────────────────────────────────────────


class ScienceArticle(Base):
    """Science exploration articles (science module)."""

    __tablename__ = "science_article"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    difficulty: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name="ck_science_difficulty",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_science_difficulty", "difficulty"),
    )


# ── Math ──────────────────────────────────────────────────


class MathQuestion(Base):
    """Math questions with four options (math module)."""

    __tablename__ = "math_question"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    difficulty: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "difficulty IN ("
            "'within_10_add_subtract','within_10_multiply_divide',"
            "'two_digit_add_subtract','two_digit_multiply_divide',"
            "'three_digit_four_operations','mixed_four_operations'"
            ")",
            name="ck_math_difficulty",
        ),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "correct_option_id IN ('A','B','C','D')",
            name="ck_math_correct",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_math_difficulty", "difficulty"),
    )


# ── English ───────────────────────────────────────────────


class EnglishWord(Base):
    """English vocabulary words (english module)."""

    __tablename__ = "english_word"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    difficulty: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "difficulty IN ('grade_3','grade_4','grade_5','grade_6')",
            name="ck_english_difficulty",
        ),
        nullable=False,
    )
    chinese: Mapped[str] = mapped_column(Text, nullable=False)
    english: Mapped[str] = mapped_column(Text, nullable=False)
    phonetic: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_english_difficulty", "difficulty"),
    )


# ── Poems ─────────────────────────────────────────────────


class PoemContent(Base):
    """Chinese poems and nursery rhymes (poems module)."""

    __tablename__ = "poem_content"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    difficulty: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "difficulty IN ('enlightenment','beginner','intermediate','advanced')",
            name="ck_poem_difficulty",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    dynasty: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_reading_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_poem_difficulty", "difficulty"),
    )


# ── Music ─────────────────────────────────────────────────


class MusicTrack(Base):
    """Music tracks (music module)."""

    __tablename__ = "music_track"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "category IN ("
            "'children_song','popular_music','classical_music',"
            "'classic_music','patriotic_music','mixed'"
            ")",
            name="ck_music_category",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_srt_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_music_category", "category"),
    )


# ── Quiz ──────────────────────────────────────────────────


class QuizQuestion(Base):
    """Quiz / brain-teaser questions (quiz module)."""

    __tablename__ = "quiz_question"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    difficulty: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name="ck_quiz_difficulty",
        ),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "correct_option_id IN ('A','B','C','D')",
            name="ck_quiz_correct",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        _content_status_ck,
        Index("idx_quiz_difficulty", "difficulty"),
    )
