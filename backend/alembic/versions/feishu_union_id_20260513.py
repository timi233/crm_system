"""add feishu_union_id to users

Revision ID: feishu_union_id_20260513
Revises: work_reports_20260513
Create Date: 2026-05-13

"""

from alembic import op


revision = "feishu_union_id_20260513"
down_revision = "work_reports_20260513"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS feishu_union_id VARCHAR(255)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_feishu_union_id ON users(feishu_union_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_feishu_union_id ON users(feishu_union_id)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_feishu_union_id")
    op.execute("DROP INDEX IF EXISTS uq_users_feishu_union_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS feishu_union_id")
