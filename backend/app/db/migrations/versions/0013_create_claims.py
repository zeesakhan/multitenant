"""create claims table

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_number", sa.String(100), nullable=False),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("member_id", sa.String(36), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_type", sa.Enum(
            "hospitalization", "outpatient", "pharmacy", "dental", "vision",
            "maternity", "emergency", "other",
            name="claim_type_enum"
        ), nullable=False),
        sa.Column("status", sa.Enum(
            "submitted", "under_review", "approved", "rejected", "paid", "closed", "withdrawn",
            name="claim_status_enum"
        ), nullable=False, server_default="submitted"),
        sa.Column("incident_date", sa.DateTime, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("claimed_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_claims_claim_number", "claims", ["claim_number"])
    op.create_index("ix_claims_policy", "claims", ["policy_id"])
    op.create_index("ix_claims_tenant_status", "claims", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("claims")
    op.execute("DROP TYPE IF EXISTS claim_type_enum")
    op.execute("DROP TYPE IF EXISTS claim_status_enum")
