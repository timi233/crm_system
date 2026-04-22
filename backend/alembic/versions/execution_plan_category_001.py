"""add plan_category to execution_plans

Revision ID: execution_plan_category_001
Revises: follow_up_optimization_001
Create Date: 2026-04-21

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "execution_plan_category_001"
down_revision = "follow_up_optimization_001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("execution_plans")}
    indexes = {index["name"] for index in inspector.get_indexes("execution_plans")}

    if "plan_category" not in columns:
        op.add_column(
            "execution_plans",
            sa.Column(
                "plan_category",
                sa.String(length=20),
                nullable=False,
                server_default="general",
            ),
        )

    if "ix_execution_plans_plan_category" not in indexes:
        op.create_index(
            "ix_execution_plans_plan_category",
            "execution_plans",
            ["plan_category"],
            unique=False,
        )

    op.execute(
        """
        UPDATE execution_plans
        SET plan_category = 'general'
        WHERE plan_category IS NULL OR plan_category = ''
        """
    )

    op.alter_column(
        "execution_plans",
        "plan_category",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="general",
    )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("execution_plans")}
    indexes = {index["name"] for index in inspector.get_indexes("execution_plans")}

    if "ix_execution_plans_plan_category" in indexes:
        op.drop_index("ix_execution_plans_plan_category", table_name="execution_plans")

    if "plan_category" in columns:
        op.drop_column("execution_plans", "plan_category")
