"""create content tables (6 learning modules)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-29 10:15:00.000000

"""
# ruff: noqa: E501 (migration files use auto-generated long lines)
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'b8c9d0e1f2a3'
down_revision: str | Sequence[str] | None = 'a7b8c9d0e1f2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Science articles ──────────────────────────────
    op.create_table(
        'science_article',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'difficulty', sa.Text(),
            sa.CheckConstraint(
                "difficulty IN ('beginner','intermediate','advanced')",
                name='ck_science_difficulty',
            ),
            nullable=False,
        ),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status'),
    )
    op.create_index('idx_science_difficulty', 'science_article', ['difficulty'])

    # ── Math questions ────────────────────────────────
    op.create_table(
        'math_question',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'difficulty', sa.Text(),
            sa.CheckConstraint(
                "difficulty IN ("
                "'within_10_add_subtract','within_10_multiply_divide',"
                "'two_digit_add_subtract','two_digit_multiply_divide',"
                "'three_digit_four_operations','mixed_four_operations'"
                ")", name='ck_math_difficulty',
            ),
            nullable=False,
        ),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column(
            'correct_option_id', sa.Text(),
            sa.CheckConstraint("correct_option_id IN ('A','B','C','D')", name='ck_math_correct'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status_math'),
    )
    op.create_index('idx_math_difficulty', 'math_question', ['difficulty'])

    # ── English words ─────────────────────────────────
    op.create_table(
        'english_word',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'difficulty', sa.Text(),
            sa.CheckConstraint(
                "difficulty IN ('grade_3','grade_4','grade_5','grade_6')",
                name='ck_english_difficulty',
            ),
            nullable=False,
        ),
        sa.Column('chinese', sa.Text(), nullable=False),
        sa.Column('english', sa.Text(), nullable=False),
        sa.Column('phonetic', sa.Text(), nullable=True),
        sa.Column('example_sentence', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status_english'),
    )
    op.create_index('idx_english_difficulty', 'english_word', ['difficulty'])

    # ── Poems ─────────────────────────────────────────
    op.create_table(
        'poem_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'difficulty', sa.Text(),
            sa.CheckConstraint(
                "difficulty IN ('enlightenment','beginner','intermediate','advanced')",
                name='ck_poem_difficulty',
            ),
            nullable=False,
        ),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('dynasty', sa.Text(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('follow_reading_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status_poem'),
    )
    op.create_index('idx_poem_difficulty', 'poem_content', ['difficulty'])

    # ── Music tracks ──────────────────────────────────
    op.create_table(
        'music_track',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'category', sa.Text(),
            sa.CheckConstraint(
                "category IN ("
                "'children_song','popular_music','classical_music',"
                "'classic_music','patriotic_music','mixed'"
                ")", name='ck_music_category',
            ),
            nullable=False,
        ),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('audio_srt_url', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status_music'),
    )
    op.create_index('idx_music_category', 'music_track', ['category'])

    # ── Quiz questions ────────────────────────────────
    op.create_table(
        'quiz_question',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'difficulty', sa.Text(),
            sa.CheckConstraint(
                "difficulty IN ('beginner','intermediate','advanced')",
                name='ck_quiz_difficulty',
            ),
            nullable=False,
        ),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column(
            'correct_option_id', sa.Text(),
            sa.CheckConstraint("correct_option_id IN ('A','B','C','D')", name='ck_quiz_correct'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'published'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_content_status_quiz'),
    )
    op.create_index('idx_quiz_difficulty', 'quiz_question', ['difficulty'])


def downgrade() -> None:
    op.drop_table('quiz_question')
    op.drop_table('music_track')
    op.drop_table('poem_content')
    op.drop_table('english_word')
    op.drop_table('math_question')
    op.drop_table('science_article')
