"""create coverages and rate_cards tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coverages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("coverage_type", sa.Enum("hospitalization", "outpatient", "dental", "vision", "maternity", "mental_health", "prescription", "preventive", "emergency", "wellness", name="coverage_type_enum"), nullable=False),
        sa.Column("limit_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("copay", sa.Numeric(10, 2), nullable=True),
        sa.Column("coinsurance_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_coverages_plan", "coverages", ["plan_id"])

    op.create_table(
        "rate_cards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rates", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rate_cards_product", "rate_cards", ["product_id"])
    op.create_index("ix_rate_cards_plan", "rate_cards", ["plan_id"])
    op.create_index("ix_rate_cards_effective", "rate_cards", ["tenant_id", "effective_date", "expiry_date"])


def downgrade() -> None:
    op.drop_table("rate_cards")
    op.drop_table("coverages")
    op.execute("DROP TYPE IF EXISTS coverage_type_enum")
