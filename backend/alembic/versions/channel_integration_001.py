"""Channel integration: add channel_id to leads

Revision ID: channel_integration_001
Revises: product_installations_001
Create Date: 2026-04-16

"""

from alembic import op
import sqlalchemy as sa

revision = "channel_integration_001"
down_revision = "product_installations_001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "leads",
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=True),
    )
    op.create_index("ix_leads_channel_id", "leads", ["channel_id"])


def downgrade():
    op.drop_index("ix_leads_channel_id", table_name="leads")
    op.drop_column("leads", "channel_id")
