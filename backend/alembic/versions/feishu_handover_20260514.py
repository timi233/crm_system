"""add feishu sync tracking and handover tables

Revision ID: feishu_handover_20260514
Revises: feishu_message_status_20260513
Create Date: 2026-05-14

"""

from alembic import op


revision = "feishu_handover_20260514"
down_revision = "feishu_message_status_20260513"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE TABLE IF NOT EXISTS feishu_org_sync_runs ("
        "id SERIAL PRIMARY KEY, "
        "started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), "
        "completed_at TIMESTAMP WITH TIME ZONE, "
        "status VARCHAR(20) NOT NULL DEFAULT 'running', "
        "total_seen INTEGER DEFAULT 0, "
        "created_count INTEGER DEFAULT 0, "
        "updated_count INTEGER DEFAULT 0, "
        "left_detected_count INTEGER DEFAULT 0, "
        "trigger VARCHAR(20) NOT NULL DEFAULT 'manual', "
        "triggered_by_user_id INTEGER REFERENCES users(id), "
        "error_message TEXT"
        ")"
    )

    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS feishu_last_seen_at TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS feishu_left_at TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS feishu_employment_status VARCHAR(20) DEFAULT 'active'"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS feishu_last_sync_run_id INTEGER REFERENCES feishu_org_sync_runs(id)"
    )

    op.execute(
        "CREATE TABLE IF NOT EXISTS employee_handover_requests ("
        "id SERIAL PRIMARY KEY, "
        "from_user_id INTEGER NOT NULL REFERENCES users(id), "
        "to_user_id INTEGER REFERENCES users(id), "
        "initiated_by_user_id INTEGER REFERENCES users(id), "
        "team_manager_user_id INTEGER REFERENCES users(id), "
        "sync_run_id INTEGER REFERENCES feishu_org_sync_runs(id), "
        "status VARCHAR(30) NOT NULL DEFAULT 'pending_assignment', "
        "scope_config JSON, "
        "preview_summary JSON, "
        "execution_summary JSON, "
        "notification_id INTEGER, "
        "feishu_message_id VARCHAR(100), "
        "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), "
        "decided_at TIMESTAMP WITH TIME ZONE, "
        "executed_at TIMESTAMP WITH TIME ZONE, "
        "error_message TEXT"
        ")"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employee_handover_requests_from_user_id ON employee_handover_requests(from_user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employee_handover_requests_status ON employee_handover_requests(status)"
    )

    op.execute(
        "CREATE TABLE IF NOT EXISTS employee_handover_logs ("
        "id SERIAL PRIMARY KEY, "
        "handover_request_id INTEGER NOT NULL REFERENCES employee_handover_requests(id), "
        "entity_type VARCHAR(50) NOT NULL, "
        "entity_id INTEGER NOT NULL, "
        "field_name VARCHAR(50) NOT NULL, "
        "from_user_id INTEGER, "
        "to_user_id INTEGER, "
        "operation VARCHAR(20) NOT NULL DEFAULT 'transfer', "
        "remark_appended TEXT, "
        "executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
        ")"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employee_handover_logs_request_id ON employee_handover_logs(handover_request_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employee_handover_logs_entity ON employee_handover_logs(entity_type, entity_id)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS employee_handover_logs")
    op.execute("DROP TABLE IF EXISTS employee_handover_requests")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS feishu_last_sync_run_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS feishu_employment_status")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS feishu_left_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS feishu_last_seen_at")
    op.execute("DROP TABLE IF EXISTS feishu_org_sync_runs")