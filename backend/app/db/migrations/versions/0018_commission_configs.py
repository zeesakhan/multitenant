"""Add commission_configs table

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commission_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("insurer_pct", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("broker_pct", sa.Numeric(5, 2), nullable=False, server_default="15.50"),
        sa.Column("tpa_pct", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_commission_configs_tenant_id", "commission_configs", ["tenant_id"])
    op.create_index("ix_commission_configs_broker_id", "commission_configs", ["broker_id"])
    op.create_index("ix_commission_configs_plan_id", "commission_configs", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_commission_configs_plan_id", "commission_configs")
    op.drop_index("ix_commission_configs_broker_id", "commission_configs")
    op.drop_index("ix_commission_configs_tenant_id", "commission_configs")
    op.drop_table("commission_configs")
