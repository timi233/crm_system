"""Change dispatch_records.work_order_id to integer FK.

Revision ID: dispatch_record_work_order_id_integer
Revises: technician_approval_001
Create Date: 2026-04-27 15:11:00.000000

"""

from alembic import context, op
import sqlalchemy as sa


revision = "dispatch_record_wo_001"
down_revision = "technician_approval_001"
branch_labels = None
depends_on = None


FK_NAME = "fk_dispatch_records_work_order_id_work_orders"


def upgrade():
    if context.is_offline_mode():
        op.execute(
            """
            ALTER TABLE dispatch_records
            DROP CONSTRAINT IF EXISTS dispatch_records_work_order_id_key
            """
        )
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id DROP NOT NULL
            """
        )
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id TYPE INTEGER
            USING CASE
                WHEN work_order_id ~ '^[0-9]+$' THEN work_order_id::integer
                ELSE NULL
            END
            """
        )
        op.execute(
            f"""
            ALTER TABLE dispatch_records
            ADD CONSTRAINT {FK_NAME}
            FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
            ON DELETE SET NULL NOT VALID
            """
        )
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("dispatch_records"):
        return

    constraints = {
        item["name"] for item in inspector.get_unique_constraints("dispatch_records")
    }
    if "dispatch_records_work_order_id_key" in constraints:
        op.drop_constraint(
            "dispatch_records_work_order_id_key",
            "dispatch_records",
            type_="unique",
        )

    fk_constraints = {
        item["name"] for item in inspector.get_foreign_keys("dispatch_records")
    }
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id DROP NOT NULL
            """
        )
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id TYPE INTEGER
            USING CASE
                WHEN work_order_id ~ '^[0-9]+$' THEN work_order_id::integer
                ELSE NULL
            END
            """
        )
        if FK_NAME not in fk_constraints:
            op.execute(
                f"""
                ALTER TABLE dispatch_records
                ADD CONSTRAINT {FK_NAME}
                FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
                ON DELETE SET NULL NOT VALID
                """
            )
    else:
        with op.batch_alter_table("dispatch_records") as batch_op:
            batch_op.alter_column(
                "work_order_id",
                existing_type=sa.String(length=100),
                type_=sa.Integer(),
                nullable=True,
            )
            if FK_NAME not in fk_constraints:
                batch_op.create_foreign_key(
                    FK_NAME,
                    "work_orders",
                    ["work_order_id"],
                    ["id"],
                    ondelete="SET NULL",
                )


def downgrade():
    if context.is_offline_mode():
        op.execute(f"ALTER TABLE dispatch_records DROP CONSTRAINT IF EXISTS {FK_NAME}")
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id TYPE VARCHAR(100)
            USING work_order_id::text
            """
        )
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("dispatch_records"):
        return

    fk_constraints = {
        item["name"] for item in inspector.get_foreign_keys("dispatch_records")
    }
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        if FK_NAME in fk_constraints:
            op.drop_constraint(FK_NAME, "dispatch_records", type_="foreignkey")
        op.execute(
            """
            ALTER TABLE dispatch_records
            ALTER COLUMN work_order_id TYPE VARCHAR(100)
            USING work_order_id::text
            """
        )
    else:
        with op.batch_alter_table("dispatch_records") as batch_op:
            if FK_NAME in fk_constraints:
                batch_op.drop_constraint(FK_NAME, type_="foreignkey")
            batch_op.alter_column(
                "work_order_id",
                existing_type=sa.Integer(),
                type_=sa.String(length=100),
                nullable=True,
            )
