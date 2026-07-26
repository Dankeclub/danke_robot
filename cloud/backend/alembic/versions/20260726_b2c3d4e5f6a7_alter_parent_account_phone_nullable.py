"""alter parent_account phone fields to nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make phone fields nullable; replace unique constraint with conditional index."""
    # Drop old unique constraint
    op.drop_constraint('parent_account_phone_hash_key', 'parent_account', type_='unique')

    # Make phone columns nullable
    op.alter_column('parent_account', 'phone_e164', nullable=True)
    op.alter_column('parent_account', 'phone_hash', nullable=True)
    op.alter_column('parent_account', 'phone_masked', nullable=True)

    # Create conditional unique index
    op.create_index(
        'idx_parent_account_phone_hash',
        'parent_account',
        ['phone_hash'],
        unique=True,
        postgresql_where=sa.text('phone_hash IS NOT NULL'),
    )


def downgrade() -> None:
    """Restore phone fields to non-nullable with plain unique constraint."""
    op.drop_index('idx_parent_account_phone_hash', 'parent_account')
    op.alter_column('parent_account', 'phone_masked', nullable=False)
    op.alter_column('parent_account', 'phone_hash', nullable=False)
    op.alter_column('parent_account', 'phone_e164', nullable=False)
    op.create_unique_constraint('parent_account_phone_hash_key', 'parent_account', ['phone_hash'])
