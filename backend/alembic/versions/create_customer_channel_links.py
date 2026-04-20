"""create customer channel links table

Revision ID: create_customer_channel_links
Revises: product_installations_001
Create Date: 2026-04-17 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "create_customer_channel_links"
down_revision = "channel_integration_001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("customer_channel_links"):
        op.create_table(
            "customer_channel_links",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("channel_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("discount_rate", sa.DECIMAL(precision=5, scale=4), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["terminal_customers.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = {index["name"] for index in inspector.get_indexes("customer_channel_links")}
    customer_idx = op.f("ix_customer_channel_links_customer_id")
    id_idx = op.f("ix_customer_channel_links_id")
    if customer_idx not in indexes:
        op.create_index(
            customer_idx, "customer_channel_links", ["customer_id"], unique=False
        )
    if id_idx not in indexes:
        op.create_index(id_idx, "customer_channel_links", ["id"], unique=False)
    if "uq_customer_active_primary_channel" not in indexes:
        op.create_index(
            "uq_customer_active_primary_channel",
            "customer_channel_links",
            ["customer_id"],
            postgresql_where=sa.text("role = '主渠道' AND end_date IS NULL"),
            unique=True,
        )

    op.execute(
        """
        INSERT INTO customer_channel_links (customer_id, channel_id, role, start_date, end_date)
        SELECT id, channel_id, '主渠道', CURRENT_DATE, NULL
        FROM terminal_customers tc
        WHERE tc.channel_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1
            FROM customer_channel_links ccl
            WHERE ccl.customer_id = tc.id
              AND ccl.channel_id = tc.channel_id
              AND ccl.role = '主渠道'
              AND ccl.end_date IS NULL
          )
        """
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("customer_channel_links"):
        indexes = {
            index["name"] for index in inspector.get_indexes("customer_channel_links")
        }
        if "uq_customer_active_primary_channel" in indexes:
            op.drop_index(
                "uq_customer_active_primary_channel", table_name="customer_channel_links"
            )
        id_idx = op.f("ix_customer_channel_links_id")
        customer_idx = op.f("ix_customer_channel_links_customer_id")
        if id_idx in indexes:
            op.drop_index(id_idx, table_name="customer_channel_links")
        if customer_idx in indexes:
            op.drop_index(customer_idx, table_name="customer_channel_links")
        op.drop_table("customer_channel_links")
