"""Phase 1: Create new module tables (channel management and dispatch)

Revision ID: phase1_new_tables
Revises: phase1_extend_tables
Create Date: 2026-04-13

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase1_new_tables"
down_revision = "phase1_extend_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "channel_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("permission_level", sa.String(20), nullable=False),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("assigned_by", sa.Integer(), nullable=True),
        sa.Column(
            "target_responsibility",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
    )
    op.create_index(
        "ix_channel_assignments_user_id", "channel_assignments", ["user_id"]
    )
    op.create_index(
        "ix_channel_assignments_channel_id", "channel_assignments", ["channel_id"]
    )

    op.create_table(
        "unified_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("performance_target", sa.NUMERIC(10, 2), nullable=True),
        sa.Column("opportunity_target", sa.NUMERIC(10, 2), nullable=True),
        sa.Column("project_count_target", sa.Integer(), nullable=True),
        sa.Column("development_goal", sa.Text(), nullable=True),
        sa.Column(
            "achieved_performance", sa.NUMERIC(10, 2), server_default="0", nullable=True
        ),
        sa.Column(
            "achieved_opportunity", sa.NUMERIC(10, 2), server_default="0", nullable=True
        ),
        sa.Column(
            "achieved_project_count", sa.Integer(), server_default="0", nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index(
        "ix_unified_targets_target_type", "unified_targets", ["target_type"]
    )
    op.create_index("ix_unified_targets_channel_id", "unified_targets", ["channel_id"])
    op.create_index("ix_unified_targets_user_id", "unified_targets", ["user_id"])
    op.create_index("ix_unified_targets_year", "unified_targets", ["year"])
    op.create_index("ix_unified_targets_quarter", "unified_targets", ["quarter"])

    op.create_table(
        "execution_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_type", sa.String(20), nullable=False),
        sa.Column("plan_period", sa.String(20), nullable=False),
        sa.Column("plan_content", sa.Text(), nullable=False),
        sa.Column("execution_status", sa.Text(), nullable=True),
        sa.Column("key_obstacles", sa.Text(), nullable=True),
        sa.Column("next_steps", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="planned", nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_execution_plans_channel_id", "execution_plans", ["channel_id"])
    op.create_index("ix_execution_plans_user_id", "execution_plans", ["user_id"])
    op.create_index("ix_execution_plans_plan_type", "execution_plans", ["plan_type"])
    op.create_index(
        "ix_execution_plans_plan_period", "execution_plans", ["plan_period"]
    )
    op.create_index("ix_execution_plans_status", "execution_plans", ["status"])

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cuid_id", sa.String(50), unique=True, nullable=True),
        sa.Column("work_order_no", sa.String(50), unique=True, nullable=False),
        sa.Column("order_type", sa.String(10), server_default="CF", nullable=False),
        sa.Column("submitter_id", sa.Integer(), nullable=False),
        sa.Column("related_sales_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_contact", sa.String(100), nullable=True),
        sa.Column("customer_phone", sa.String(50), nullable=True),
        sa.Column("has_channel", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("channel_name", sa.String(100), nullable=True),
        sa.Column("channel_contact", sa.String(100), nullable=True),
        sa.Column("channel_phone", sa.String(50), nullable=True),
        sa.Column("manufacturer_contact", sa.String(100), nullable=True),
        sa.Column("work_type", sa.String(50), nullable=True),
        sa.Column("priority", sa.String(20), server_default="NORMAL", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="PENDING", nullable=False),
        sa.Column("estimated_start_date", sa.Date(), nullable=True),
        sa.Column("estimated_start_period", sa.String(10), nullable=True),
        sa.Column("estimated_end_date", sa.Date(), nullable=True),
        sa.Column("estimated_end_period", sa.String(10), nullable=True),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("service_summary", sa.Text(), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(20), nullable=True),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_sales_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
    )
    op.create_index("ix_work_orders_cuid_id", "work_orders", ["cuid_id"], unique=True)
    op.create_index(
        "ix_work_orders_work_order_no", "work_orders", ["work_order_no"], unique=True
    )
    op.create_index("ix_work_orders_order_type", "work_orders", ["order_type"])
    op.create_index("ix_work_orders_submitter_id", "work_orders", ["submitter_id"])
    op.create_index(
        "ix_work_orders_related_sales_id", "work_orders", ["related_sales_id"]
    )
    op.create_index("ix_work_orders_channel_id", "work_orders", ["channel_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_source_type", "work_orders", ["source_type"])
    op.create_index("ix_work_orders_lead_id", "work_orders", ["lead_id"])
    op.create_index("ix_work_orders_opportunity_id", "work_orders", ["opportunity_id"])
    op.create_index("ix_work_orders_project_id", "work_orders", ["project_id"])

    op.create_table(
        "work_order_technicians",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("technician_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["technician_id"], ["users.id"]),
        sa.UniqueConstraint(
            "work_order_id", "technician_id", name="uq_work_order_technician"
        ),
    )
    op.create_index(
        "ix_work_order_technicians_work_order_id",
        "work_order_technicians",
        ["work_order_id"],
    )
    op.create_index(
        "ix_work_order_technicians_technician_id",
        "work_order_technicians",
        ["technician_id"],
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("quality_rating", sa.Integer(), nullable=False),
        sa.Column("response_rating", sa.Integer(), nullable=False),
        sa.Column("customer_feedback", sa.Text(), nullable=True),
        sa.Column("improvement_suggestion", sa.Text(), nullable=True),
        sa.Column("recommend", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("evaluator_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["evaluator_id"], ["users.id"]),
    )
    op.create_index(
        "ix_evaluations_work_order_id", "evaluations", ["work_order_id"], unique=True
    )

    op.create_table(
        "knowledge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem_type", sa.String(100), nullable=True),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(255), nullable=True),
        sa.Column(
            "source_type", sa.String(20), server_default="manual", nullable=False
        ),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_title", "knowledge", ["title"])
    op.create_index("ix_knowledge_problem_type", "knowledge", ["problem_type"])


def downgrade():
    op.drop_table("knowledge")
    op.drop_table("evaluations")
    op.drop_table("work_order_technicians")
    op.drop_table("work_orders")
    op.drop_table("execution_plans")
    op.drop_table("unified_targets")
    op.drop_table("channel_assignments")
