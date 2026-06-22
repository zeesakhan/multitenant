"""Add medical questionnaire and biometric fields to members

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("members", sa.Column("medical_questionnaire", sa.JSON(), nullable=True))
    op.add_column("members", sa.Column("pregnancy_questionnaire", sa.JSON(), nullable=True))
    op.add_column("members", sa.Column("height_cm", sa.Numeric(5, 1), nullable=True))
    op.add_column("members", sa.Column("weight_kg", sa.Numeric(5, 1), nullable=True))
    op.add_column("members", sa.Column("marital_status", sa.String(20), nullable=True))


def downgrade() -> None:
    for col in ["marital_status", "weight_kg", "height_cm", "pregnancy_questionnaire", "medical_questionnaire"]:
        op.drop_column("members", col)
