"""Patch applications: add product_id, plan_id; make quote_id nullable

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("product_id", sa.String(36), nullable=True))
    op.add_column("applications", sa.Column("plan_id", sa.String(36), nullable=True))
    op.alter_column("applications", "quote_id", nullable=True)
    op.create_foreign_key("applications_product_id_fkey", "applications", "products", ["product_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("applications_plan_id_fkey", "applications", "plans", ["plan_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("applications_plan_id_fkey", "applications", type_="foreignkey")
    op.drop_constraint("applications_product_id_fkey", "applications", type_="foreignkey")
    op.alter_column("applications", "quote_id", nullable=False)
    op.drop_column("applications", "plan_id")
    op.drop_column("applications", "product_id")
