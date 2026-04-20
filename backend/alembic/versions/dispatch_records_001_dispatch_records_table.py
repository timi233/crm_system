"""Create dispatch_records table

Revision ID: dispatch_records_001
Revises:
Create Date: 2026-04-10 18:35:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = "dispatch_records_001"
down_revision = "add_lead_source_channel"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dispatch_records"):
        op.create_table(
            "dispatch_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("work_order_id", sa.String(100), nullable=False, unique=True),
            sa.Column("work_order_no", sa.String(50), nullable=True),
            sa.Column("source_type", sa.String(20), nullable=False),
            sa.Column("lead_id", sa.Integer(), nullable=True),
            sa.Column("opportunity_id", sa.Integer(), nullable=True),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
            sa.Column("previous_status", sa.String(50), nullable=True),
            sa.Column("status_updated_at", sa.TIMESTAMP, nullable=True),
            sa.Column("order_type", sa.String(10), nullable=True),
            sa.Column("customer_name", sa.String(255), nullable=True),
            sa.Column("technician_ids", ARRAY(sa.Text), nullable=True),
            sa.Column("priority", sa.String(20), nullable=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("dispatch_data", JSONB, nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP,
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP,
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("dispatched_at", sa.TIMESTAMP, nullable=True),
            sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(
                ["opportunity_id"], ["opportunities.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.CheckConstraint(
                "source_type IN ('lead', 'opportunity', 'project')",
                name="check_source_type",
            ),
        )

    indexes = {index["name"] for index in inspector.get_indexes("dispatch_records")}
    if "idx_dispatch_lead" not in indexes:
        op.create_index(
            "idx_dispatch_lead",
            "dispatch_records",
            ["lead_id"],
            postgresql_where=sa.text("lead_id IS NOT NULL"),
        )
    if "idx_dispatch_opportunity" not in indexes:
        op.create_index(
            "idx_dispatch_opportunity",
            "dispatch_records",
            ["opportunity_id"],
            postgresql_where=sa.text("opportunity_id IS NOT NULL"),
        )
    if "idx_dispatch_project" not in indexes:
        op.create_index(
            "idx_dispatch_project",
            "dispatch_records",
            ["project_id"],
            postgresql_where=sa.text("project_id IS NOT NULL"),
        )
    if "idx_dispatch_status" not in indexes:
        op.create_index("idx_dispatch_status", "dispatch_records", ["status"])
    if "idx_dispatch_created_at" not in indexes:
        op.create_index(
            "idx_dispatch_created_at",
            "dispatch_records",
            ["created_at"],
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC"},
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("dispatch_records"):
        indexes = {index["name"] for index in inspector.get_indexes("dispatch_records")}
        if "idx_dispatch_created_at" in indexes:
            op.drop_index("idx_dispatch_created_at", table_name="dispatch_records")
        if "idx_dispatch_status" in indexes:
            op.drop_index("idx_dispatch_status", table_name="dispatch_records")
        if "idx_dispatch_project" in indexes:
            op.drop_index("idx_dispatch_project", table_name="dispatch_records")
        if "idx_dispatch_opportunity" in indexes:
            op.drop_index("idx_dispatch_opportunity", table_name="dispatch_records")
        if "idx_dispatch_lead" in indexes:
            op.drop_index("idx_dispatch_lead", table_name="dispatch_records")
        op.drop_table("dispatch_records")
