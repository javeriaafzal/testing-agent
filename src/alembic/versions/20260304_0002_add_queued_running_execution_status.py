"""add queued and running execution statuses

Revision ID: 20260304_0002
Revises: 20260303_0001
Create Date: 2026-03-04 00:02:00
"""

from alembic import op


revision = "20260304_0002"
down_revision = "20260303_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE execution_status ADD VALUE IF NOT EXISTS 'QUEUED'")
    op.execute("ALTER TYPE execution_status ADD VALUE IF NOT EXISTS 'RUNNING'")


def downgrade() -> None:
    op.execute("UPDATE executions SET status = 'FAIL' WHERE status IN ('QUEUED', 'RUNNING')")
    op.execute("ALTER TYPE execution_status RENAME TO execution_status_old")
    op.execute("CREATE TYPE execution_status AS ENUM ('PASS', 'FAIL')")
    op.execute(
        """
        ALTER TABLE executions
        ALTER COLUMN status TYPE execution_status
        USING status::text::execution_status
        """
    )
    op.execute("DROP TYPE execution_status_old")
