"""create learning_module_config

Revision ID: a7b8c9d0e1f2
Revises: d4e5f6a7b8d0
Create Date: 2026-07-29 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'a7b8c9d0e1f2'
down_revision: str | Sequence[str] | None = 'd4e5f6a7b8d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'learning_module_config',
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
            'module',
            sa.Text(),
            sa.CheckConstraint(
                "module IN ('science','math','english','poems','music','quiz')",
                name='ck_config_module',
            ),
            nullable=False,
        ),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('difficulty', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column(
            'batch_size',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('10'),
        ),
        sa.Column(
            'min_repeat_interval_seconds',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('604800'),
        ),
        sa.Column(
            'config_version',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('1'),
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
        sa.UniqueConstraint('child_id', 'module', name='uq_config_child_module'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_config_child', 'learning_module_config', ['child_id'])


def downgrade() -> None:
    op.drop_table('learning_module_config')
