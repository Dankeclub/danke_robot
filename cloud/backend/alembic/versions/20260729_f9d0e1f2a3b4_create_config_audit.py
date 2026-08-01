"""create config_audit

Revision ID: f9d0e1f2a3b4
Revises: e8d9d0e1f2a3
Create Date: 2026-07-29 13:00:00.000000

"""
# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9d0e1f2a3b4"
down_revision: str | None = "e8d9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "config_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column(
            "module",
            sa.Text(),
            sa.CheckConstraint(
                "module IN ('science','math','english','poems','music','quiz')",
                name="ck_audit_module",
            ),
            nullable=False,
        ),
        sa.Column("changed_by", sa.Text(), nullable=False),
        sa.Column(
            "old_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "new_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["child_id"], ["child.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_child", "config_audit", ["child_id"])
    op.create_index("idx_audit_child_module", "config_audit", ["child_id", "module"])
    op.create_index("idx_audit_created", "config_audit", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_created", table_name="config_audit")
    op.drop_index("idx_audit_child_module", table_name="config_audit")
    op.drop_index("idx_audit_child", table_name="config_audit")
    op.drop_table("config_audit")
