"""follow up optimization fields for channel visits

Revision ID: follow_up_optimization_001
Revises: channel_contacts_001
Create Date: 2026-04-21

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "follow_up_optimization_001"
down_revision = "channel_contacts_001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("follow_ups")}

    if "follow_up_type" not in columns:
        op.add_column(
            "follow_ups",
            sa.Column(
                "follow_up_type",
                sa.String(length=20),
                nullable=False,
                server_default="business",
            ),
        )

    if "visit_location" not in columns:
        op.add_column(
            "follow_ups",
            sa.Column("visit_location", sa.String(length=100), nullable=True),
        )

    if "visit_attendees" not in columns:
        op.add_column(
            "follow_ups",
            sa.Column("visit_attendees", sa.String(length=255), nullable=True),
        )

    if "visit_purpose" not in columns:
        op.add_column(
            "follow_ups",
            sa.Column("visit_purpose", sa.String(length=100), nullable=True),
        )

    op.alter_column("follow_ups", "follow_up_conclusion", existing_type=sa.String(length=30), nullable=True)

    op.execute(
        """
        UPDATE follow_ups
        SET follow_up_type = CASE
            WHEN channel_id IS NOT NULL
                 AND lead_id IS NULL
                 AND opportunity_id IS NULL
                 AND project_id IS NULL
            THEN 'channel'
            ELSE 'business'
        END
        WHERE follow_up_type IS NULL OR follow_up_type = ''
        """
    )

    op.alter_column(
        "follow_ups",
        "follow_up_type",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="business",
    )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("follow_ups")}

    if "visit_purpose" in columns:
        op.drop_column("follow_ups", "visit_purpose")
    if "visit_attendees" in columns:
        op.drop_column("follow_ups", "visit_attendees")
    if "visit_location" in columns:
        op.drop_column("follow_ups", "visit_location")
    if "follow_up_type" in columns:
        op.drop_column("follow_ups", "follow_up_type")
