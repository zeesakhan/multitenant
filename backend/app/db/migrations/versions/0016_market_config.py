"""Add market_configs table for per-tenant configurable values

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_market_configs_tenant_id", "market_configs", ["tenant_id"])
    op.create_unique_constraint("uq_market_configs_tenant_key", "market_configs", ["tenant_id", "key"])


def downgrade() -> None:
    op.drop_constraint("uq_market_configs_tenant_key", "market_configs", type_="unique")
    op.drop_index("ix_market_configs_tenant_id", "market_configs")
    op.drop_table("market_configs")
