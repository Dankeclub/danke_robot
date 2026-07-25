"""create parent_account

Revision ID: dd627dffb8b5
Revises: 
Create Date: 2026-07-25 10:56:30.602626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'dd627dffb8b5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'parent_account',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('phone_e164', sa.Text(), nullable=False),
        sa.Column('phone_hash', sa.Text(), nullable=False),
        sa.Column('phone_masked', sa.Text(), nullable=False),
        sa.Column('nickname', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('wx_openid', sa.Text(), nullable=True),
        sa.Column('wx_unionid', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Text(),
            server_default=sa.text("'active'"),
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
        sa.UniqueConstraint('phone_hash'),
        sa.UniqueConstraint('wx_openid'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('parent_account')
