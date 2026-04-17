"""Create product_installations table

Revision ID: product_installations_001
Revises:
Create Date: 2024-04-15

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "product_installations_001"
down_revision = "phase1_new_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_installations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("manufacturer", sa.String(100), nullable=False),
        sa.Column("product_type", sa.String(100), nullable=False),
        sa.Column("product_model", sa.String(100), nullable=True),
        sa.Column("license_scale", sa.String(100), nullable=True),
        sa.Column("system_version", sa.String(100), nullable=True),
        sa.Column("online_date", sa.Date(), nullable=True),
        sa.Column("maintenance_expiry", sa.Date(), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("password", sa.String(255), nullable=True),
        sa.Column("login_url", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["terminal_customers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "manufacturer IN ('爱数', '安恒', 'IPG', '绿盟', '深信服', '其他')",
            name="check_manufacturer",
        ),
    )

    op.create_index("idx_pi_customer", "product_installations", ["customer_id"])
    op.create_index("idx_pi_manufacturer", "product_installations", ["manufacturer"])
    op.create_index("idx_pi_online_date", "product_installations", ["online_date"])


def downgrade():
    op.drop_index("idx_pi_online_date", "product_installations")
    op.drop_index("idx_pi_manufacturer", "product_installations")
    op.drop_index("idx_pi_customer", "product_installations")
    op.drop_table("product_installations")
