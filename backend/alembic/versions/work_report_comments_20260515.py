"""add work report comments table

Revision ID: work_report_comments_20260515
Revises: feishu_handover_fk_20260514
Create Date: 2026-05-15

"""

from alembic import op


revision = "work_report_comments_20260515"
down_revision = "feishu_handover_fk_20260514"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS work_report_comments (
            id SERIAL PRIMARY KEY,
            report_id INTEGER NOT NULL REFERENCES work_reports(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_report_comments_report_id ON work_report_comments(report_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_report_comments_user_id ON work_report_comments(user_id)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_work_report_comments_user_id")
    op.execute("DROP INDEX IF EXISTS ix_work_report_comments_report_id")
    op.execute("DROP TABLE IF EXISTS work_report_comments")
