"""Add str_records table (Suspicious Transaction Reports)

Revision ID: 0023
Revises: 0022
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "str_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("str_reference", sa.String(50), nullable=True),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("nature_of_suspicion", sa.Text(), nullable=True),
        sa.Column("subject_details", sa.JSON(), nullable=True),
        sa.Column("transaction_details", sa.JSON(), nullable=True),
        sa.Column("approver_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("audit_trail", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_str_records_tenant_id", "str_records", ["tenant_id"])
    op.create_index("ix_str_records_application_id", "str_records", ["application_id"])
    op.create_index("ix_str_records_status", "str_records", ["status"])
    op.create_unique_constraint("uq_str_records_reference", "str_records", ["str_reference"])


def downgrade() -> None:
    op.drop_constraint("uq_str_records_reference", "str_records", type_="unique")
    op.drop_index("ix_str_records_status", "str_records")
    op.drop_index("ix_str_records_application_id", "str_records")
    op.drop_index("ix_str_records_tenant_id", "str_records")
    op.drop_table("str_records")
