"""create parent_child

Revision ID: e5f6a7b8c9d0
Revises: f8c2a9e1b3d7
Create Date: 2026-07-25 13:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: str | Sequence[str] | None = 'f8c2a9e1b3d7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'parent_child',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('parent_account.id'),
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            'is_default',
            sa.Boolean(),
            server_default=sa.text('FALSE'),
            nullable=False,
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_id', 'child_id'),
    )
    op.create_index('idx_parent_child_parent', 'parent_child', ['parent_id'])
    op.create_index('idx_parent_child_child', 'parent_child', ['child_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('parent_child')
