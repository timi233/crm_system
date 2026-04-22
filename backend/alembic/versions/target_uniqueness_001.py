"""add uniqueness indexes for annual and quarterly targets

Revision ID: target_uniqueness_001
Revises: execution_plan_category_001
Create Date: 2026-04-21

"""

from alembic import op


revision = "target_uniqueness_001"
down_revision = "execution_plan_category_001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_unified_targets_annual_scope
        ON unified_targets (
            target_type,
            year,
            COALESCE(channel_id, -1),
            COALESCE(user_id, -1)
        )
        WHERE quarter IS NULL AND month IS NULL
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_unified_targets_quarter_scope
        ON unified_targets (
            target_type,
            year,
            quarter,
            COALESCE(channel_id, -1),
            COALESCE(user_id, -1)
        )
        WHERE quarter IS NOT NULL AND month IS NULL
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_targets_yearly_user_year
        ON sales_targets (user_id, target_year)
        WHERE target_type = 'yearly'
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_targets_quarterly_user_year_period
        ON sales_targets (user_id, target_year, target_period)
        WHERE target_type = 'quarterly'
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_sales_targets_quarterly_user_year_period")
    op.execute("DROP INDEX IF EXISTS uq_sales_targets_yearly_user_year")
    op.execute("DROP INDEX IF EXISTS uq_unified_targets_quarter_scope")
    op.execute("DROP INDEX IF EXISTS uq_unified_targets_annual_scope")
