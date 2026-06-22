"""Patch members: add passport_number, emirates_id, nationality, visa_type, document_expiry, place_of_birth

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("members", sa.Column("passport_number", sa.String(50), nullable=True))
    op.add_column("members", sa.Column("emirates_id", sa.String(25), nullable=True))
    op.add_column("members", sa.Column("nationality", sa.String(100), nullable=True))
    op.add_column("members", sa.Column("visa_type", sa.String(80), nullable=True))
    op.add_column("members", sa.Column("document_expiry", sa.Date(), nullable=True))
    op.add_column("members", sa.Column("place_of_birth", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("members", "place_of_birth")
    op.drop_column("members", "document_expiry")
    op.drop_column("members", "visa_type")
    op.drop_column("members", "nationality")
    op.drop_column("members", "emirates_id")
    op.drop_column("members", "passport_number")
