"""create learning_event

Revision ID: d4e5f6a7b8d0
Revises: c3d4e5f6a7b8
Create Date: 2026-07-26 09:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'd4e5f6a7b8d0'
down_revision: str | Sequence[str] | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create learning_event table."""
    op.create_table(
        'learning_event',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'device_id',
            sa.Text(),
            sa.ForeignKey('device_binding.device_id'),
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'event_id',
            sa.Text(),
            nullable=False,
            comment='Client-generated idempotency key (UUID v4)',
        ),
        sa.Column(
            'event_type',
            sa.Text(),
            nullable=False,
            comment='e.g. learning.session.start, learning.answer.submit',
        ),
        sa.Column(
            'module',
            sa.Text(),
            nullable=True,
            comment='One of: science, math, english, poems, music, quiz',
        ),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Event occurrence time from the device',
        ),
        sa.Column(
            'payload',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment='Arbitrary event data',
        ),
        sa.Column(
            'received_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
            comment='Server receive time',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.UniqueConstraint('device_id', 'event_id', name='uq_learning_event_device_event'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_learning_event_device', 'learning_event', ['device_id'])
    op.create_index('idx_learning_event_child', 'learning_event', ['child_id'])
    op.create_index('idx_learning_event_type', 'learning_event', ['event_type'])
    op.create_index('idx_learning_event_timestamp', 'learning_event', ['timestamp'])


def downgrade() -> None:
    """Drop learning_event table."""
    op.drop_table('learning_event')
