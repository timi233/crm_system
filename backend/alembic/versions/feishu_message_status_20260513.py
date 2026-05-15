"""add feishu message status fields to work_order_technicians

Revision ID: feishu_message_status_20260513
Revises: feishu_union_id_20260513
Create Date: 2026-05-13

"""

from alembic import op


revision = "feishu_message_status_20260513"
down_revision = "feishu_union_id_20260513"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS feishu_message_status VARCHAR(20) DEFAULT 'PENDING'"
    )
    op.execute(
        "ALTER TABLE work_order_technicians ADD COLUMN IF NOT EXISTS feishu_message_error TEXT"
    )


def downgrade():
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS feishu_message_status"
    )
    op.execute(
        "ALTER TABLE work_order_technicians DROP COLUMN IF EXISTS feishu_message_error"
    )
