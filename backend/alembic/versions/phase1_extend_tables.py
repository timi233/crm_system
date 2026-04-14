"""Phase 1: Extend users and channels tables for cross-system compatibility

Revision ID: phase1_extend_tables
Revises:
Create Date: 2026-04-13

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase1_extend_tables"
down_revision = "dispatch_records_001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("uuid_id", postgresql.UUID(as_uuid=True), unique=True, nullable=True),
    )
    op.add_column(
        "users", sa.Column("cuid_id", sa.String(255), unique=True, nullable=True)
    )
    op.add_column("users", sa.Column("functional_role", sa.String(50), nullable=True))
    op.add_column(
        "users", sa.Column("responsibility_role", sa.String(50), nullable=True)
    )
    op.add_column("users", sa.Column("department", sa.String(100), nullable=True))
    op.add_column(
        "users",
        sa.Column("user_status", sa.String(20), nullable=True, server_default="ACTIVE"),
    )
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "users", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column("users", sa.Column("full_name", sa.String(255), nullable=True))

    op.create_index("ix_users_uuid_id", "users", ["uuid_id"], unique=True)
    op.create_index("ix_users_cuid_id", "users", ["cuid_id"], unique=True)

    op.add_column(
        "channels",
        sa.Column("uuid_id", postgresql.UUID(as_uuid=True), unique=True, nullable=True),
    )
    op.add_column("channels", sa.Column("business_type", sa.String(50), nullable=True))
    op.add_column("channels", sa.Column("channel_status", sa.String(20), nullable=True))
    op.add_column("channels", sa.Column("description", sa.Text, nullable=True))
    op.add_column(
        "channels", sa.Column("contact_person", sa.String(100), nullable=True)
    )
    op.add_column("channels", sa.Column("contact_email", sa.String(255), nullable=True))
    op.add_column("channels", sa.Column("contact_phone", sa.String(50), nullable=True))
    op.add_column(
        "channels",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "channels", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column("channels", sa.Column("created_by", sa.Integer, nullable=True))
    op.add_column("channels", sa.Column("last_modified_by", sa.Integer, nullable=True))

    op.alter_column("channels", "created_at", new_column_name="created_at_legacy")
    op.alter_column("channels", "updated_at", new_column_name="updated_at_legacy")

    op.create_index("ix_channels_uuid_id", "channels", ["uuid_id"], unique=True)
    op.create_index("ix_channels_business_type", "channels", ["business_type"])
    op.create_index("ix_channels_channel_status", "channels", ["channel_status"])

    op.create_foreign_key(
        "fk_channels_created_by", "channels", "users", ["created_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_channels_last_modified_by",
        "channels",
        "users",
        ["last_modified_by"],
        ["id"],
    )


def downgrade():
    op.drop_index("ix_channels_channel_status", "channels")
    op.drop_index("ix_channels_business_type", "channels")
    op.drop_index("ix_channels_uuid_id", "channels")

    op.drop_constraint("fk_channels_last_modified_by", "channels", type_="foreignkey")
    op.drop_constraint("fk_channels_created_by", "channels", type_="foreignkey")

    op.alter_column("channels", "created_at_legacy", new_column_name="created_at")
    op.alter_column("channels", "updated_at_legacy", new_column_name="updated_at")

    op.drop_column("channels", "last_modified_by")
    op.drop_column("channels", "created_by")
    op.drop_column("channels", "updated_at")
    op.drop_column("channels", "created_at")
    op.drop_column("channels", "contact_phone")
    op.drop_column("channels", "contact_email")
    op.drop_column("channels", "contact_person")
    op.drop_column("channels", "description")
    op.drop_column("channels", "channel_status")
    op.drop_column("channels", "business_type")
    op.drop_column("channels", "uuid_id")

    op.drop_index("ix_users_cuid_id", "users")
    op.drop_index("ix_users_uuid_id", "users")

    op.drop_column("users", "full_name")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
    op.drop_column("users", "user_status")
    op.drop_column("users", "department")
    op.drop_column("users", "responsibility_role")
    op.drop_column("users", "functional_role")
    op.drop_column("users", "cuid_id")
    op.drop_column("users", "uuid_id")
