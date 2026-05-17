"""create policies table

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_number", sa.String(100), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quote_id", sa.String(36), sa.ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("member_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("total_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Enum(
            "active", "inactive", "expired", "cancelled", "suspended", "lapsed", "renewed",
            name="policy_status_enum"
        ), nullable=False, server_default="active"),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "policy_number", name="uq_policies_tenant_number"),
    )
    op.create_index("ix_policies_tenant_status", "policies", ["tenant_id", "status"])
    op.create_index("ix_policies_customer_email", "policies", ["tenant_id", "customer_email"])


def downgrade() -> None:
    op.drop_table("policies")
    op.execute("DROP TYPE IF EXISTS policy_status_enum")
