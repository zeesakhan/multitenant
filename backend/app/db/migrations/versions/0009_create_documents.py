"""create document_templates and document_uploads tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("template_type", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("required_fields", sa.JSON, nullable=True),
        sa.Column("mime_types", sa.JSON, nullable=True),
        sa.Column("max_size_kb", sa.Integer, nullable=False, server_default="5120"),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_templates_tenant_code", "document_templates", ["tenant_id", "code"])
    op.create_index("ix_document_templates_type", "document_templates", ["template_type"])

    op.create_table(
        "document_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("document_type", sa.Enum("policy_document", "quote_document", "application_form", "invoice", "endorsement", "renewal_notice", "claims_form", "medical_report", "id_proof", "address_proof", "income_proof", name="document_type_enum"), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("validation_status", sa.Enum("pending", "valid", "invalid", name="document_validation_status_enum"), nullable=False, server_default="pending"),
        sa.Column("validation_errors", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_uploads_tenant_entity", "document_uploads", ["tenant_id", "entity_type", "entity_id"])
    op.create_index("ix_document_uploads_type", "document_uploads", ["tenant_id", "document_type"])
    op.create_index("ix_document_uploads_uploaded_by", "document_uploads", ["uploaded_by"])
    op.create_index("ix_document_uploads_validation", "document_uploads", ["validation_status"])


def downgrade() -> None:
    op.drop_table("document_uploads")
    op.drop_table("document_templates")
    op.execute("DROP TYPE IF EXISTS document_type_enum")
    op.execute("DROP TYPE IF EXISTS document_validation_status_enum")
