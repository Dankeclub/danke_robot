"""relax daily_task module constraint to allow NULL

Revision ID: a1b2c4d5e6f7
Revises: a1b2c3d4e5f7
Create Date: 2026-07-30 10:01:00.000000

"""
from collections.abc import Sequence

from alembic import op

revision: str = 'a1b2c4d5e6f7'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE daily_task ALTER COLUMN module DROP NOT NULL")
    op.execute("ALTER TABLE daily_task DROP CONSTRAINT IF EXISTS ck_task_module")
    op.execute(
        "ALTER TABLE daily_task ADD CONSTRAINT ck_task_module "
        "CHECK (module IS NULL OR module IN "
        "('science','math','english','poems','music','quiz'))"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE daily_task SET module = 'custom' WHERE module IS NULL"
    )
    op.execute("ALTER TABLE daily_task DROP CONSTRAINT IF EXISTS ck_task_module")
    op.execute(
        "ALTER TABLE daily_task ADD CONSTRAINT ck_task_module "
        "CHECK (module IN ('science','math','english','poems','music','quiz'))"
    )
    op.execute("ALTER TABLE daily_task ALTER COLUMN module SET NOT NULL")
