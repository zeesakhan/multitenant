"""create products and plans tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("status", sa.Enum("draft", "active", "inactive", "archived", name="product_status_enum"), nullable=False, server_default="draft"),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_products_tenant_status", "products", ["tenant_id", "status"])
    op.create_unique_constraint("uq_products_tenant_code", "products", ["tenant_id", "code"])

    op.create_table(
        "plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("plan_type", sa.Enum("individual", "family", "group", "senior", name="plan_type_enum"), nullable=False, server_default="individual"),
        sa.Column("base_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("coverage_details", sa.JSON, nullable=True),
        sa.Column("included_services", sa.JSON, nullable=True),
        sa.Column("exclusions", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_plans_product", "plans", ["product_id"])
    op.create_unique_constraint("uq_plans_tenant_product_code", "plans", ["tenant_id", "product_id", "code"])


def downgrade() -> None:
    op.drop_table("plans")
    op.drop_table("products")
    op.execute("DROP TYPE IF EXISTS product_status_enum")
    op.execute("DROP TYPE IF EXISTS plan_type_enum")
