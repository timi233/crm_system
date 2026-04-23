"""Create dispatch_records table

Revision ID: dispatch_records_001
Revises: add_lead_source_channel
Create Date: 2026-04-10 18:35:00.000000

"""

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = "dispatch_records_001"
down_revision = "add_lead_source_channel"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        # Offline mode: Safe DDL without introspection
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS dispatch_records (
                id SERIAL PRIMARY KEY,
                work_order_id VARCHAR(100) NOT NULL UNIQUE,
                work_order_no VARCHAR(50),
                source_type VARCHAR(20) NOT NULL,
                lead_id INTEGER,
                opportunity_id INTEGER,
                project_id INTEGER,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                previous_status VARCHAR(50),
                status_updated_at TIMESTAMP,
                order_type VARCHAR(10),
                customer_name VARCHAR(255),
                technician_ids TEXT[],
                priority VARCHAR(20),
                description TEXT,
                dispatch_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                dispatched_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
                CONSTRAINT check_source_type CHECK (source_type IN ('lead', 'opportunity', 'project'))
            )
            """
        )

        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dispatch_lead ON dispatch_records(lead_id) WHERE lead_id IS NOT NULL"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dispatch_opportunity ON dispatch_records(opportunity_id) WHERE opportunity_id IS NOT NULL"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dispatch_project ON dispatch_records(project_id) WHERE project_id IS NOT NULL"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dispatch_status ON dispatch_records(status)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dispatch_created_at ON dispatch_records(created_at DESC)"
        )
    else:
        # Online mode: Original introspection logic
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
                sa.Column(
                    "status", sa.String(50), nullable=False, server_default="pending"
                ),
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
                sa.ForeignKeyConstraint(
                    ["project_id"], ["projects.id"], ondelete="SET NULL"
                ),
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
    if context.is_offline_mode():
        # Offline mode: Safe drop statements
        op.execute("DROP INDEX IF EXISTS idx_dispatch_created_at")
        op.execute("DROP INDEX IF EXISTS idx_dispatch_status")
        op.execute("DROP INDEX IF EXISTS idx_dispatch_project")
        op.execute("DROP INDEX IF EXISTS idx_dispatch_opportunity")
        op.execute("DROP INDEX IF EXISTS idx_dispatch_lead")
        op.execute("DROP TABLE IF EXISTS dispatch_records")
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if inspector.has_table("dispatch_records"):
            indexes = {
                index["name"] for index in inspector.get_indexes("dispatch_records")
            }
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
