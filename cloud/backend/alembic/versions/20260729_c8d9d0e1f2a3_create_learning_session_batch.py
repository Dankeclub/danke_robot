"""create learning_session, learning_batch, batch_item

Revision ID: c8d9d0e1f2a3
Revises: b8c9d0e1f2a3
Create Date: 2026-07-29 11:00:00.000000

"""
# ruff: noqa: E501 (migration files use auto-generated long lines)
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'c8d9d0e1f2a3'
down_revision: str | Sequence[str] | None = 'b8c9d0e1f2a3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Learning session ──────────────────────────────
    op.create_table(
        'learning_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'child_id', postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'), nullable=False,
        ),
        sa.Column(
            'module', sa.Text(),
            sa.CheckConstraint(
                "module IN ('science','math','english','poems','music','quiz')",
                name='ck_session_module',
            ),
            nullable=False,
        ),
        sa.Column(
            'source', sa.Text(),
            sa.CheckConstraint(
                "source IN ('today_task','free_learning','task_extension','ws_navigation')",
                name='ck_session_source',
            ),
            nullable=False,
        ),
        sa.Column('task_id', sa.Text(), nullable=True),
        sa.Column('navigation_id', sa.Text(), nullable=True),
        sa.Column(
            'status', sa.Text(),
            sa.CheckConstraint(
                "status IN ('active','completed','expired')",
                name='ck_session_status',
            ),
            nullable=False, server_default=sa.text("'active'"),
        ),
        sa.Column(
            'config_snapshot', postgresql.JSONB(),
            nullable=False, server_default=sa.text("'{}'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_session_child', 'learning_session', ['child_id'])
    op.create_index('idx_session_module', 'learning_session', ['module'])

    # ── Learning batch ────────────────────────────────
    op.create_table(
        'learning_batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'session_id', postgresql.UUID(as_uuid=True),
            sa.ForeignKey('learning_session.id'), nullable=False,
        ),
        sa.Column('module', sa.Text(), nullable=False),
        sa.Column('sequence_no', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'config_snapshot', postgresql.JSONB(),
            nullable=False, server_default=sa.text("'{}'"),
        ),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'status', sa.Text(),
            sa.CheckConstraint(
                "status IN ('active','completed')",
                name='ck_batch_status',
            ),
            nullable=False, server_default=sa.text("'active'"),
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('session_id', 'sequence_no', name='uq_batch_session_seq'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_batch_session', 'learning_batch', ['session_id'])

    # ── Batch item ────────────────────────────────────
    op.create_table(
        'batch_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'batch_id', postgresql.UUID(as_uuid=True),
            sa.ForeignKey('learning_batch.id'), nullable=False,
        ),
        sa.Column('content_id', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Text(), nullable=False),
        sa.Column(
            'content_snapshot', postgresql.JSONB(),
            nullable=False, server_default=sa.text("'{}'"),
        ),
        sa.Column('item_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_batch_item_batch', 'batch_item', ['batch_id'])


def downgrade() -> None:
    op.drop_table('batch_item')
    op.drop_table('learning_batch')
    op.drop_table('learning_session')
