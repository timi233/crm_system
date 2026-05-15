"""expand user department path length

Revision ID: feishu_department_path_20260514
Revises: feishu_handover_20260514
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa


revision = "feishu_department_path_20260514"
down_revision = "feishu_handover_20260514"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "users",
        "department",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "users",
        "department",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
