"""phase3 new tables — behavior_event, parent_message, navigation_instruction,
notification_settings, notification, file_upload

Revision ID: d5e6f7a8b9c0
Revises: a1b2c4d5e6f7
Create Date: 2026-08-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "a1b2c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- behavior_event ---
    op.create_table(
        "behavior_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Text(),
            sa.CheckConstraint(
                "event_type IN ('focus','posture','location','zone')",
                name="ck_behavior_event_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "score",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Score 0-100, higher is better for focus/posture",
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Detailed metrics: {duration_seconds, zone_name, ...}",
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When the behavior was observed (device time)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["child.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_behavior_child", "behavior_event", ["child_id"])
    op.create_index(
        "idx_behavior_child_type_time",
        "behavior_event",
        ["child_id", "event_type", "recorded_at"],
    )

    # --- parent_message ---
    op.create_table(
        "parent_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column(
            "direction",
            sa.Text(),
            sa.CheckConstraint(
                "direction IN ('parent_to_child','child_to_parent')",
                name="ck_msg_direction",
            ),
            nullable=False,
        ),
        sa.Column(
            "msg_type",
            sa.Text(),
            sa.CheckConstraint(
                "msg_type IN ('text','image','audio','task_card')",
                name="ck_msg_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "content",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("replied_to_id", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["child.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.id"]),
        sa.ForeignKeyConstraint(["replied_to_id"], ["parent_message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_msg_child", "parent_message", ["child_id"])
    op.create_index("idx_msg_child_parent", "parent_message", ["child_id", "parent_id"])
    op.create_index("idx_msg_created", "parent_message", ["created_at"])

    # --- navigation_instruction ---
    op.create_table(
        "navigation_instruction",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column(
            "destination",
            sa.Text(),
            sa.CheckConstraint(
                "destination IN ('learning','chat','parent_messages')",
                name="ck_nav_destination",
            ),
            nullable=False,
        ),
        sa.Column("route_key", sa.Text(), nullable=False),
        sa.Column("module", sa.Text(), nullable=True),
        sa.Column("custom_batch_size", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            sa.CheckConstraint(
                "status IN ('pending','delivered','expired')",
                name="ck_nav_status",
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["child.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_nav_child", "navigation_instruction", ["child_id"])
    op.create_index("idx_nav_child_status", "navigation_instruction", ["child_id", "status"])

    # --- notification_settings ---
    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column(
            "settings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("dnd_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("dnd_start_time", sa.Time(), nullable=True),
        sa.Column("dnd_end_time", sa.Time(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["child.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id", name="uq_notif_settings_child"),
    )
    op.create_index("idx_notif_settings_child", "notification_settings", ["child_id"])

    # --- notification ---
    op.create_table(
        "notification",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("notif_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["child.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notif_parent", "notification", ["parent_id"])
    op.create_index("idx_notif_parent_read", "notification", ["parent_id", "is_read"])
    op.create_index("idx_notif_created", "notification", ["created_at"])

    # --- file_upload ---
    op.create_table(
        "file_upload",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column(
            "purpose",
            sa.Text(),
            sa.CheckConstraint(
                "purpose IN ('parent_message_image','parent_message_audio','parent_avatar','child_avatar')",
                name="ck_file_purpose",
            ),
            nullable=False,
        ),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            sa.CheckConstraint(
                "status IN ('pending','available','expired')",
                name="ck_file_status",
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_file_parent", "file_upload", ["parent_id"])
    op.create_index("idx_file_status", "file_upload", ["status"])


def downgrade() -> None:
    op.drop_table("file_upload")
    op.drop_table("notification")
    op.drop_table("notification_settings")
    op.drop_table("navigation_instruction")
    op.drop_table("parent_message")
    op.drop_table("behavior_event")
