"""Extend user_type_enum with compliance_officer and finance

Revision ID: 0025
Revises: 0024
Create Date: 2026-06-22
"""
from typing import Union
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_type_enum ADD VALUE IF NOT EXISTS 'compliance_officer'")
    op.execute("ALTER TYPE user_type_enum ADD VALUE IF NOT EXISTS 'finance'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op
    pass
