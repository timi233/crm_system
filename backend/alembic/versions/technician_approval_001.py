"""add approval fields to work_order_technicians

Revision ID: technician_approval_001
Revises: entity_products_001
Create Date: 2026-04-24

"""

from alembic import op
import sqlalchemy as sa


revision = "technician_approval_001"
down_revision = "entity_products_001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_order_technicians_status ON work_order_technicians(status)"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS approval_instance_code VARCHAR(100)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_order_technicians_approval_instance_code ON work_order_technicians(approval_instance_code)"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'PENDING'"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_work_order_technicians_idempotency_key ON work_order_technicians(idempotency_key) WHERE idempotency_key IS NOT NULL"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP WITH TIME ZONE"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP WITH TIME ZONE"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS feishu_message_id VARCHAR(100)"
    )

    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS approval_created_at TIMESTAMP WITH TIME ZONE"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_work_order_technicians_idempotency_key")
    op.execute("DROP INDEX IF EXISTS idx_work_order_technicians_approval_instance_code")
    op.execute("DROP INDEX IF EXISTS idx_work_order_technicians_status")
    op.execute("ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS status")
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS approval_instance_code"
    )
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS approval_status"
    )
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS idempotency_key"
    )
    op.execute("ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS accepted_at")
    op.execute("ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS rejected_at")
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS feishu_message_id"
    )
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS approval_created_at"
    )
