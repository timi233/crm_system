"""add encrypted product installation credential columns

Revision ID: product_installation_credential_ciphertext_20260515
Revises: work_report_comments_20260515
Create Date: 2026-05-15

"""

from alembic import op


revision = "product_installation_credential_ciphertext_20260515"
down_revision = "work_report_comments_20260515"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE product_installations ADD COLUMN IF NOT EXISTS username_ciphertext TEXT"
    )
    op.execute(
        "ALTER TABLE product_installations ADD COLUMN IF NOT EXISTS password_ciphertext TEXT"
    )
    op.execute(
        "ALTER TABLE product_installations ADD COLUMN IF NOT EXISTS login_url_ciphertext TEXT"
    )


def downgrade():
    op.execute(
        "ALTER TABLE product_installations DROP COLUMN IF EXISTS login_url_ciphertext"
    )
    op.execute(
        "ALTER TABLE product_installations DROP COLUMN IF EXISTS password_ciphertext"
    )
    op.execute(
        "ALTER TABLE product_installations DROP COLUMN IF EXISTS username_ciphertext"
    )
