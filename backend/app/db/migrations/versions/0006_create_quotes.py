"""create quotes table

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quote_number", sa.String(100), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("total_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Enum("draft", "sent", "viewed", "expired", "converted", "declined", name="quote_status_enum"), nullable=False, server_default="draft"),
        sa.Column("breakdown", sa.JSON, nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_quotes_tenant_status", "quotes", ["tenant_id", "status"])
    op.create_index("ix_quotes_created_by", "quotes", ["created_by"])
    op.create_index("ix_quotes_valid_until", "quotes", ["valid_until"])
    op.create_unique_constraint("uq_quotes_tenant_number", "quotes", ["tenant_id", "quote_number"])


def downgrade() -> None:
    op.drop_table("quotes")
    op.execute("DROP TYPE IF EXISTS quote_status_enum")
