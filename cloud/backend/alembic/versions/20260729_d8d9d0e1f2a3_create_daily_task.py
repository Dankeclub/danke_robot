"""create daily_task

Revision ID: d8d9d0e1f2a3
Revises: c8d9d0e1f2a3
Create Date: 2026-07-29 11:30:00.000000

"""
# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'd8d9d0e1f2a3'
down_revision: str | Sequence[str] | None = 'c8d9d0e1f2a3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'daily_task',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'child_id', postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'), nullable=False,
        ),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column(
            'module', sa.Text(),
            sa.CheckConstraint(
                "module IN ('science','math','english','poems','music','quiz')",
                name='ck_task_module',
            ),
            nullable=False,
        ),
        sa.Column(
            'task_category', sa.Text(),
            sa.CheckConstraint(
                "task_category IN ('learning','lifestyle','sports','custom')",
                name='ck_task_category',
            ),
            nullable=False, server_default=sa.text("'learning'"),
        ),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column(
            'status', sa.Text(),
            sa.CheckConstraint(
                "status IN ('assigned','claimed','in_progress','completed','expired')",
                name='ck_task_status',
            ),
            nullable=False, server_default=sa.text("'assigned'"),
        ),
        sa.Column(
            'config_snapshot', postgresql.JSONB(),
            nullable=False, server_default=sa.text("'{}'"),
        ),
        sa.Column('progress_completed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('progress_total', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('child_id', 'business_date', 'module', name='uq_task_child_date_module'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_task_child_date', 'daily_task', ['child_id', 'business_date'])
    op.create_index('idx_task_status', 'daily_task', ['status'])


def downgrade() -> None:
    op.drop_table('daily_task')
