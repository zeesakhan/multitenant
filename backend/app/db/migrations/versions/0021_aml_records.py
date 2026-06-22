"""Add aml_records table

Revision ID: 0021
Revises: 0020
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aml_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.String(36), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cleared_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clearance_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aml_records_tenant_id", "aml_records", ["tenant_id"])
    op.create_index("ix_aml_records_application_id", "aml_records", ["application_id"])
    op.create_index("ix_aml_records_status", "aml_records", ["status"])


def downgrade() -> None:
    op.drop_index("ix_aml_records_status", "aml_records")
    op.drop_index("ix_aml_records_application_id", "aml_records")
    op.drop_index("ix_aml_records_tenant_id", "aml_records")
    op.drop_table("aml_records")
