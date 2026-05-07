"""redesign sales target system

Revision ID: sales_target_redesign_2026
Revises: dispatch_record_work_order_id_integer
Create Date: 2026-05-07 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "sales_target_redesign_2026"
down_revision = "dispatch_record_wo_001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.delete(sa.table("sales_targets")))

    op.add_column(
        "sales_targets",
        sa.Column(
            "gross_profit_target",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0.0"),
        ),
    )

    op.create_table(
        "actual_performance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.Integer(),
            sa.ForeignKey("sales_targets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("amount_actual", sa.Float(), nullable=False),
        sa.Column("gross_profit_actual", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table("actual_performance")
    op.drop_column("sales_targets", "gross_profit_target")
