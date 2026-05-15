"""ensure notification tables and handover foreign key

Revision ID: feishu_handover_fk_20260514
Revises: feishu_department_path_20260514
Create Date: 2026-05-14

"""

from alembic import op


revision = "feishu_handover_fk_20260514"
down_revision = "feishu_department_path_20260514"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            notification_type VARCHAR(30) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            entity_type VARCHAR(30),
            entity_id INTEGER,
            entity_code VARCHAR(50),
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL,
            read_at TIMESTAMP
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_notification_reads (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            entity_type VARCHAR(30) NOT NULL,
            entity_id INTEGER NOT NULL,
            notification_type VARCHAR(30) NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_notification_reads_user_id "
        "ON user_notification_reads(user_id)"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'employee_handover_requests_notification_id_fkey'
            ) THEN
                ALTER TABLE employee_handover_requests
                ADD CONSTRAINT employee_handover_requests_notification_id_fkey
                FOREIGN KEY (notification_id) REFERENCES notifications(id);
            END IF;
        END
        $$;
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE employee_handover_requests
        DROP CONSTRAINT IF EXISTS employee_handover_requests_notification_id_fkey
        """
    )
