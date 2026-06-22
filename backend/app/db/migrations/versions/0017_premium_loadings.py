"""Add premium_loadings table

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "premium_loadings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.String(36), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=True),
        sa.Column("loading_type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("applied_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_premium_loadings_application_id", "premium_loadings", ["application_id"])
    op.create_index("ix_premium_loadings_tenant_id", "premium_loadings", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_premium_loadings_tenant_id", "premium_loadings")
    op.drop_index("ix_premium_loadings_application_id", "premium_loadings")
    op.drop_table("premium_loadings")
