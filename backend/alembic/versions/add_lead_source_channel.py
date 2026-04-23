"""add_lead_source_channel

Revision ID: add_lead_source_channel
Revises: create_customer_channel_links
Create Date: 2026-04-17

"""

from alembic import op, context
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_lead_source_channel"
down_revision = "create_customer_channel_links"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        # Offline mode: Safe DDL without introspection
        op.execute(
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_channel_id INTEGER"
        )

        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_leads_source_channel_id_channels'
                ) THEN
                    ALTER TABLE leads
                    ADD CONSTRAINT fk_leads_source_channel_id_channels
                    FOREIGN KEY (source_channel_id) REFERENCES channels(id);
                END IF;
            END $$;
            """
        )

        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_leads_source_channel_id ON leads(source_channel_id)"
        )

        # Data backfill for offline mode
        op.execute(
            "UPDATE leads SET source_channel_id = channel_id WHERE channel_id IS NOT NULL AND source_channel_id IS NULL"
        )
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        columns = {column["name"] for column in inspector.get_columns("leads")}
        indexes = {index["name"] for index in inspector.get_indexes("leads")}

        if "source_channel_id" not in columns:
            op.add_column(
                "leads", sa.Column("source_channel_id", sa.Integer(), nullable=True)
            )
            op.create_foreign_key(
                "fk_leads_source_channel_id_channels",
                "leads",
                "channels",
                ["source_channel_id"],
                ["id"],
            )
        if "idx_leads_source_channel_id" not in indexes:
            op.create_index(
                "idx_leads_source_channel_id", "leads", ["source_channel_id"]
            )

        # 回填存量数据：把现有 lead.channel_id 回填到 source_channel_id
        op.execute(
            "UPDATE leads SET source_channel_id = channel_id WHERE channel_id IS NOT NULL AND source_channel_id IS NULL"
        )


def downgrade():
    if context.is_offline_mode():
        # Offline mode: Safe drop statements
        op.execute("DROP INDEX IF EXISTS idx_leads_source_channel_id")
        op.execute(
            """
            ALTER TABLE leads
            DROP CONSTRAINT IF EXISTS fk_leads_source_channel_id_channels
            """
        )
        op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS source_channel_id")
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        indexes = {index["name"] for index in inspector.get_indexes("leads")}
        columns = {column["name"] for column in inspector.get_columns("leads")}
        foreign_keys = {fk.get("name") for fk in inspector.get_foreign_keys("leads")}
        if "idx_leads_source_channel_id" in indexes:
            op.drop_index("idx_leads_source_channel_id", table_name="leads")
        if "fk_leads_source_channel_id_channels" in foreign_keys:
            op.drop_constraint(
                "fk_leads_source_channel_id_channels", "leads", type_="foreignkey"
            )
        if "source_channel_id" in columns:
            op.drop_column("leads", "source_channel_id")
