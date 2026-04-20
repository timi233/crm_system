"""create channel_contacts table

Revision ID: channel_contacts_001
Revises: channel_followup_leads_001
Create Date: 2026-04-20

"""

from alembic import op
import sqlalchemy as sa


revision = "channel_contacts_001"
down_revision = "channel_followup_leads_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "channel_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_channel_contacts_id", "channel_contacts", ["id"], unique=False)
    op.create_index(
        "ix_channel_contacts_channel_id", "channel_contacts", ["channel_id"], unique=False
    )


def downgrade():
    op.drop_index("ix_channel_contacts_channel_id", table_name="channel_contacts")
    op.drop_index("ix_channel_contacts_id", table_name="channel_contacts")
    op.drop_table("channel_contacts")
