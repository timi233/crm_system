"""Channel integration: add channel_id to leads

Revision ID: channel_integration_001
Revises: product_installations_001
Create Date: 2026-04-16

"""

from alembic import op, context
import sqlalchemy as sa


revision = "channel_integration_001"
down_revision = "product_installations_001"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        # Offline mode: Safe DDL without introspection
        op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS channel_id INTEGER")

        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_leads_channel_id_channels'
                ) THEN
                    ALTER TABLE leads
                    ADD CONSTRAINT fk_leads_channel_id_channels
                    FOREIGN KEY (channel_id) REFERENCES channels(id);
                END IF;
            END $$;
            """
        )

        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_leads_channel_id ON leads(channel_id)"
        )
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        columns = {column["name"] for column in inspector.get_columns("leads")}
        indexes = {index["name"] for index in inspector.get_indexes("leads")}

        if "channel_id" not in columns:
            op.add_column("leads", sa.Column("channel_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                "fk_leads_channel_id_channels",
                "leads",
                "channels",
                ["channel_id"],
                ["id"],
            )
        if "ix_leads_channel_id" not in indexes:
            op.create_index("ix_leads_channel_id", "leads", ["channel_id"])


def downgrade():
    if context.is_offline_mode():
        # Offline mode: Safe drop statements
        op.execute("DROP INDEX IF EXISTS ix_leads_channel_id")
        op.execute(
            """
            ALTER TABLE leads
            DROP CONSTRAINT IF EXISTS fk_leads_channel_id_channels
            """
        )
        op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS channel_id")
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        indexes = {index["name"] for index in inspector.get_indexes("leads")}
        columns = {column["name"] for column in inspector.get_columns("leads")}
        foreign_keys = {fk.get("name") for fk in inspector.get_foreign_keys("leads")}

        if "ix_leads_channel_id" in indexes:
            op.drop_index("ix_leads_channel_id", table_name="leads")
        if "fk_leads_channel_id_channels" in foreign_keys:
            op.drop_constraint(
                "fk_leads_channel_id_channels", "leads", type_="foreignkey"
            )
        if "channel_id" in columns:
            op.drop_column("leads", "channel_id")
