"""add_lead_source_channel

Revision ID: add_lead_source_channel
Revises: create_customer_channel_links
Create Date: 2026-04-17

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_lead_source_channel"
down_revision = "create_customer_channel_links"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("leads")}
    indexes = {index["name"] for index in inspector.get_indexes("leads")}

    if "source_channel_id" not in columns:
        op.add_column("leads", sa.Column("source_channel_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_leads_source_channel_id_channels",
            "leads",
            "channels",
            ["source_channel_id"],
            ["id"],
        )
    if "idx_leads_source_channel_id" not in indexes:
        op.create_index("idx_leads_source_channel_id", "leads", ["source_channel_id"])

    # 回填存量数据：把现有 lead.channel_id 回填到 source_channel_id
    op.execute(
        "UPDATE leads SET source_channel_id = channel_id WHERE channel_id IS NOT NULL AND source_channel_id IS NULL"
    )


def downgrade():
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
