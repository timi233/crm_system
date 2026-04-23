"""Create product_installations table

Revision ID: product_installations_001
Revises: phase1_new_tables
Create Date: 2024-04-15

"""

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "product_installations_001"
down_revision = "phase1_new_tables"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        # Offline mode: Safe DDL without introspection
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS product_installations (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES terminal_customers(id) ON DELETE CASCADE,
                manufacturer VARCHAR(100) NOT NULL,
                product_type VARCHAR(100) NOT NULL,
                product_model VARCHAR(100),
                license_scale VARCHAR(100),
                system_version VARCHAR(100),
                online_date DATE,
                maintenance_expiry DATE,
                username VARCHAR(255),
                password VARCHAR(255),
                login_url VARCHAR(255),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                CONSTRAINT check_manufacturer CHECK (manufacturer IN ('爱数', '安恒', 'IPG', '绿盟', '深信服', '其他'))
            )
            """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pi_customer
            ON product_installations(customer_id)
            """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pi_manufacturer
            ON product_installations(manufacturer)
            """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pi_online_date
            ON product_installations(online_date)
            """
        )
    else:
        # Online mode: Use original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)

        if not inspector.has_table("product_installations"):
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
                sa.ForeignKeyConstraint(
                    ["created_by_id"], ["users.id"], ondelete="SET NULL"
                ),
                sa.CheckConstraint(
                    "manufacturer IN ('爱数', '安恒', 'IPG', '绿盟', '深信服', '其他')",
                    name="check_manufacturer",
                ),
            )

        indexes = {
            index["name"] for index in inspector.get_indexes("product_installations")
        }
        if "idx_pi_customer" not in indexes:
            op.create_index("idx_pi_customer", "product_installations", ["customer_id"])
        if "idx_pi_manufacturer" not in indexes:
            op.create_index(
                "idx_pi_manufacturer", "product_installations", ["manufacturer"]
            )
        if "idx_pi_online_date" not in indexes:
            op.create_index(
                "idx_pi_online_date", "product_installations", ["online_date"]
            )


def downgrade():
    if context.is_offline_mode():
        # Offline mode: Safe drop statements
        op.execute("DROP INDEX IF EXISTS idx_pi_online_date")
        op.execute("DROP INDEX IF EXISTS idx_pi_manufacturer")
        op.execute("DROP INDEX IF EXISTS idx_pi_customer")
        op.execute("DROP TABLE IF EXISTS product_installations")
    else:
        # Online mode: Original introspection logic
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if inspector.has_table("product_installations"):
            indexes = {
                index["name"]
                for index in inspector.get_indexes("product_installations")
            }
            if "idx_pi_online_date" in indexes:
                op.drop_index("idx_pi_online_date", "product_installations")
            if "idx_pi_manufacturer" in indexes:
                op.drop_index("idx_pi_manufacturer", "product_installations")
            if "idx_pi_customer" in indexes:
                op.drop_index("idx_pi_customer", "product_installations")
            op.drop_table("product_installations")
