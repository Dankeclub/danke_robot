"""create learning_goal

Revision ID: a1b2c3d4e5f7
Revises: f9d0e1f2a3b4
Create Date: 2026-07-30 10:00:00.000000

"""
# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'a1b2c3d4e5f7'
down_revision: str | Sequence[str] | None = 'f9d0e1f2a3b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'learning_goal',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'daily_goal_minutes',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('30'),
        ),
        sa.Column(
            'module_goals',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.UniqueConstraint('child_id', name='uq_learning_goal_child'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_learning_goal_child', 'learning_goal', ['child_id'])


def downgrade() -> None:
    op.drop_table('learning_goal')
