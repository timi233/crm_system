"""add channel_id to follow_ups

Revision ID: channel_followup_leads_001
Revises: dispatch_records_001
Create Date: 2026-04-20

"""

from alembic import op, context
import sqlalchemy as sa

revision = "channel_followup_leads_001"
down_revision = "dispatch_records_001"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        # Offline mode: Safe DDL without introspection
        op.execute("ALTER TABLE follow_ups ADD COLUMN IF NOT EXISTS channel_id INTEGER")

        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_follow_ups_channel_id_channels'
                ) THEN
                    ALTER TABLE follow_ups
                    ADD CONSTRAINT fk_follow_ups_channel_id_channels
                    FOREIGN KEY (channel_id) REFERENCES channels(id);
                END IF;
            END $$;
            """
        )

        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_follow_ups_channel_id ON follow_ups(channel_id)"
        )
    else:
        # Online mode: Original introspection logic
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
    if context.is_offline_mode():
        # Offline mode: Safe drop statements
        op.execute("DROP INDEX IF EXISTS idx_follow_ups_channel_id")
        op.execute(
            """
            ALTER TABLE follow_ups
            DROP CONSTRAINT IF EXISTS fk_follow_ups_channel_id_channels
            """
        )
        op.execute("ALTER TABLE follow_ups DROP COLUMN IF EXISTS channel_id")
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        indexes = {index["name"] for index in inspector.get_indexes("follow_ups")}
        foreign_keys = {
            fk["name"]
            for fk in inspector.get_foreign_keys("follow_ups")
            if fk.get("name")
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
