"""create child

Revision ID: f8c2a9e1b3d7
Revises: e9e6605e8258
Create Date: 2026-07-25 13:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8c2a9e1b3d7'
down_revision: str | Sequence[str] | None = 'e9e6605e8258'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'child',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column('nickname', sa.Text(), nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column(
            'gender',
            sa.Text(),
            sa.CheckConstraint(
                "gender IN ('boy', 'girl', 'unknown')",
                name='ck_child_gender',
            ),
            nullable=True,
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
    )
    op.create_index('idx_child_family', 'child', ['family_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('child')
