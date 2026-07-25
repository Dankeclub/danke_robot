"""create device_binding

Revision ID: d4e5f6a7b8c9
Revises: e5f6a7b8c9d0
Create Date: 2026-07-25 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create device_binding table."""
    op.create_table(
        'device_binding',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('device_id', sa.Text(), nullable=False),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column('device_name', sa.Text(), nullable=False),
        sa.Column(
            'device_type',
            sa.Text(),
            server_default=sa.text("'car'"),
            nullable=False,
        ),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('app_version', sa.Text(), nullable=True),
        sa.Column(
            'bind_status',
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            'bound_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
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
        sa.UniqueConstraint('device_id'),
        sa.CheckConstraint(
            "device_type IN ('car', 'robot')",
            name='ck_device_binding_device_type',
        ),
        sa.CheckConstraint(
            "bind_status IN ('active', 'inactive', 'revoked')",
            name='ck_device_binding_bind_status',
        ),
    )
    op.create_index(
        'idx_device_binding_device', 'device_binding', ['device_id']
    )
    # Partial unique index: one child can have at most one active binding
    op.execute(
        "CREATE UNIQUE INDEX idx_device_binding_child_active "
        "ON device_binding(child_id) WHERE bind_status = 'active'"
    )


def downgrade() -> None:
    """Downgrade schema: drop device_binding table."""
    op.drop_table('device_binding')
