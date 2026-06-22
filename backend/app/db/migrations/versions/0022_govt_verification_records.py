"""Add govt_verification_records table

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "govt_verification_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.String(36), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overridden_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("override_justification", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_govt_verification_tenant_id", "govt_verification_records", ["tenant_id"])
    op.create_index("ix_govt_verification_application_id", "govt_verification_records", ["application_id"])
    op.create_index("ix_govt_verification_status", "govt_verification_records", ["status"])
    op.create_index("ix_govt_verification_check_type", "govt_verification_records", ["check_type"])


def downgrade() -> None:
    op.drop_index("ix_govt_verification_check_type", "govt_verification_records")
    op.drop_index("ix_govt_verification_status", "govt_verification_records")
    op.drop_index("ix_govt_verification_application_id", "govt_verification_records")
    op.drop_index("ix_govt_verification_tenant_id", "govt_verification_records")
    op.drop_table("govt_verification_records")
