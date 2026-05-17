"""create applications and application_items tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_number", sa.String(100), nullable=False),
        sa.Column("quote_id", sa.String(36), sa.ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("member_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("total_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Enum("draft", "submitted", "under_review", "pending_documents", "pending_payment", "approved", "rejected", "cancelled", "issued", name="application_status_enum"), nullable=False, server_default="draft"),
        sa.Column("breakdown", sa.JSON, nullable=True),
        sa.Column("additional_info", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_applications_tenant_status", "applications", ["tenant_id", "status"])
    op.create_index("ix_applications_quote_id", "applications", ["quote_id"])
    op.create_index("ix_applications_created_by", "applications", ["created_by"])
    op.create_unique_constraint("uq_applications_tenant_number", "applications", ["tenant_id", "application_number"])

    op.create_table(
        "application_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coverage_id", sa.String(36), sa.ForeignKey("coverages.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="application_item_status_enum"), nullable=False, server_default="pending"),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_application_items_application", "application_items", ["application_id"])
    op.create_index("ix_application_items_coverage", "application_items", ["coverage_id"])


def downgrade() -> None:
    op.drop_table("application_items")
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS application_status_enum")
    op.execute("DROP TYPE IF EXISTS application_item_status_enum")
