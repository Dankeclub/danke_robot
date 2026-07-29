"""create answer_record and wrong_answer

Revision ID: e8d9d0e1f2a3
Revises: d8d9d0e1f2a3
Create Date: 2026-07-29 12:00:00.000000

"""
# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'e8d9d0e1f2a3'
down_revision: str | Sequence[str] | None = 'd8d9d0e1f2a3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'answer_record',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_session.id'), nullable=False),
        sa.Column('batch_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('batch_item.id'), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('child.id'), nullable=False),
        sa.Column('module', sa.Text(), nullable=False),
        sa.Column('question_snapshot', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('selected_option_id', sa.Text(), nullable=False),
        sa.Column('correct_option_id', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('answer_duration_ms', sa.Integer(), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_answer_session', 'answer_record', ['session_id'])
    op.create_index('idx_answer_child', 'answer_record', ['child_id'])

    op.create_table(
        'wrong_answer',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('child.id'), nullable=False),
        sa.Column('module', sa.Text(), nullable=False),
        sa.Column('question_snapshot', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('question_id', sa.Text(), nullable=False),
        sa.Column('selected_option_id', sa.Text(), nullable=False),
        sa.Column('correct_option_id', sa.Text(), nullable=False),
        sa.Column('wrong_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('first_wrong_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_wrong_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_wrong_answer_child', 'wrong_answer', ['child_id'])
    op.create_index('idx_wrong_answer_question', 'wrong_answer', ['child_id', 'question_id'])


def downgrade() -> None:
    op.drop_table('wrong_answer')
    op.drop_table('answer_record')
