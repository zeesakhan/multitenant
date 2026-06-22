"""Add updated_at to compliance tables missing the column

Revision ID: 0026
Revises: 0025
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ["aml_records", "govt_verification_records", "notification_records", "premium_loadings"]:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'updated_at'
                ) THEN
                    ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
                END IF;
            END$$;
        """)


def downgrade() -> None:
    pass
