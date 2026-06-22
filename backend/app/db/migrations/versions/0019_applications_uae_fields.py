"""Extend applications table with UAE compliance and AML fields

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("aml_status", sa.String(20), nullable=False, server_default="clear"))
    op.add_column("applications", sa.Column("aml_risk_score", sa.Numeric(5, 2), nullable=True))
    op.add_column("applications", sa.Column("govt_check_status", sa.String(20), nullable=False, server_default="pending"))
    op.add_column("applications", sa.Column("marital_status", sa.String(20), nullable=True))
    op.add_column("applications", sa.Column("occupation", sa.String(100), nullable=True))
    op.add_column("applications", sa.Column("employer_name", sa.String(200), nullable=True))
    op.add_column("applications", sa.Column("trn", sa.String(50), nullable=True))
    op.add_column("applications", sa.Column("sponsor_type", sa.String(20), nullable=False, server_default="individual"))
    op.add_column("applications", sa.Column("existing_health_insurance", sa.String(20), nullable=True))
    op.add_column("applications", sa.Column("is_diplomatic_passport", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("applications", sa.Column("is_eid_under_process", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("applications", sa.Column("remarks", sa.JSON(), nullable=True))
    op.add_column("applications", sa.Column("premium_breakdown", sa.JSON(), nullable=True))
    op.add_column("applications", sa.Column("cover_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("applications", sa.Column("co_payment_config", sa.JSON(), nullable=True))
    op.create_index("ix_applications_aml_status", "applications", ["aml_status"])
    op.create_index("ix_applications_govt_check_status", "applications", ["govt_check_status"])


def downgrade() -> None:
    op.drop_index("ix_applications_govt_check_status", "applications")
    op.drop_index("ix_applications_aml_status", "applications")
    for col in [
        "co_payment_config", "cover_amount", "premium_breakdown", "remarks",
        "is_eid_under_process", "is_diplomatic_passport", "existing_health_insurance",
        "sponsor_type", "trn", "employer_name", "occupation", "marital_status",
        "govt_check_status", "aml_risk_score", "aml_status",
    ]:
        op.drop_column("applications", col)
