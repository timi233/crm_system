"""add work reports and department manager

Revision ID: work_reports_20260513
Revises: sales_target_redesign_2026
Create Date: 2026-05-13

"""

from alembic import op


revision = "work_reports_20260513"
down_revision = "sales_target_redesign_2026"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS department_manager_id INTEGER"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_users_department_manager_id_users'
            ) THEN
                ALTER TABLE users
                ADD CONSTRAINT fk_users_department_manager_id_users
                FOREIGN KEY (department_manager_id) REFERENCES users(id);
            END IF;
        END $$;
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_department_manager_id ON users(department_manager_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS work_reports (
            id SERIAL PRIMARY KEY,
            report_type VARCHAR(20) NOT NULL,
            report_date DATE NOT NULL,
            week_start DATE,
            week_end DATE,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            owner_role VARCHAR(50),
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            structured_snapshot JSON,
            remark TEXT,
            source_report_ids JSON,
            submitted_at TIMESTAMP WITH TIME ZONE,
            withdrawn_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_work_report_owner_type_date
        ON work_reports(owner_id, report_type, report_date)
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_reports_owner_id ON work_reports(owner_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_reports_report_date ON work_reports(report_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_reports_report_type ON work_reports(report_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_work_reports_status ON work_reports(status)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_work_reports_status")
    op.execute("DROP INDEX IF EXISTS ix_work_reports_report_type")
    op.execute("DROP INDEX IF EXISTS ix_work_reports_report_date")
    op.execute("DROP INDEX IF EXISTS ix_work_reports_owner_id")
    op.execute("DROP INDEX IF EXISTS uq_work_report_owner_type_date")
    op.execute("DROP TABLE IF EXISTS work_reports")
    op.execute("DROP INDEX IF EXISTS ix_users_department_manager_id")
    op.execute(
        "ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_department_manager_id_users"
    )
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS department_manager_id")
