"""create payments table

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_number", sa.String(100), nullable=False),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Enum(
            "pending", "processing", "success", "failed", "refunded",
            "partially_refunded", "cancelled",
            name="payment_status_enum"
        ), nullable=False, server_default="success"),
        sa.Column("method", sa.Enum(
            "card", "bank_transfer", "upi", "wallet", "cheque", "cash", "net_banking",
            name="payment_method_enum"
        ), nullable=False, server_default="bank_transfer"),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_payment_number", "payments", ["payment_number"])
    op.create_index("ix_payments_policy", "payments", ["policy_id"])
    op.create_index("ix_payments_tenant_status", "payments", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("payments")
    op.execute("DROP TYPE IF EXISTS payment_status_enum")
    op.execute("DROP TYPE IF EXISTS payment_method_enum")
