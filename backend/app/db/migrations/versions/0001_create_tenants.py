"""create tenants and brand_configs tables

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", "suspended", name="tenant_status_enum"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="UTC"),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_code", "tenants", ["code"])

    op.create_table(
        "brand_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(20), nullable=False, server_default="#1976D2"),
        sa.Column("secondary_color", sa.String(20), nullable=False, server_default="#424242"),
        sa.Column("accent_color", sa.String(20), nullable=False, server_default="#FF5722"),
        sa.Column("font_family", sa.String(100), nullable=False, server_default="Inter"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("tagline", sa.String(500), nullable=True),
        sa.Column("support_email", sa.String(255), nullable=True),
        sa.Column("support_phone", sa.String(50), nullable=True),
        sa.Column("custom_css", sa.Text, nullable=True),
        sa.Column("extra_config", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_brand_configs_tenant_id", "brand_configs", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("brand_configs")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS tenant_status_enum")
