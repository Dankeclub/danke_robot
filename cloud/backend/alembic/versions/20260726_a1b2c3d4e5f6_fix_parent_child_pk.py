"""fix parent_child composite primary key

Revision ID: a1b2c3d4e5f6
Revises: d4e5f6a7b8c9
Create Date: 2026-07-26 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace UUID PK with composite (parent_id, child_id) PK."""
    # Drop old table
    op.drop_table('parent_child')

    # Recreate with composite PK
    op.create_table(
        'parent_child',
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('parent_account.id'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
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
        sa.PrimaryKeyConstraint('parent_id', 'child_id'),
    )
    op.create_index('idx_parent_child_parent', 'parent_child', ['parent_id'])
    op.create_index('idx_parent_child_child', 'parent_child', ['child_id'])


def downgrade() -> None:
    """Restore UUID PK."""
    op.drop_table('parent_child')
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
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
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
