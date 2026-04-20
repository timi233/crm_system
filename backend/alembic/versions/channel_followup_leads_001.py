"""add channel_id to follow_ups

Revision ID: channel_followup_leads_001
Revises: dispatch_records_001
Create Date: 2026-04-20

"""
from alembic import op
import sqlalchemy as sa

revision = "channel_followup_leads_001"
down_revision = "dispatch_records_001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("follow_ups")}
    indexes = {index["name"] for index in inspector.get_indexes("follow_ups")}

    if "channel_id" not in columns:
        op.add_column(
            "follow_ups",
            sa.Column("channel_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_follow_ups_channel_id_channels",
            "follow_ups",
            "channels",
            ["channel_id"],
            ["id"],
        )

    if "idx_follow_ups_channel_id" not in indexes:
        op.create_index("idx_follow_ups_channel_id", "follow_ups", ["channel_id"])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("follow_ups")}
    foreign_keys = {
        fk["name"] for fk in inspector.get_foreign_keys("follow_ups") if fk.get("name")
    }
    columns = {column["name"] for column in inspector.get_columns("follow_ups")}

    if "idx_follow_ups_channel_id" in indexes:
        op.drop_index("idx_follow_ups_channel_id", table_name="follow_ups")
    if "fk_follow_ups_channel_id_channels" in foreign_keys:
        op.drop_constraint(
            "fk_follow_ups_channel_id_channels", "follow_ups", type_="foreignkey"
        )
    if "channel_id" in columns:
        op.drop_column("follow_ups", "channel_id")
