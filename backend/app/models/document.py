from sqlalchemy import Column, String, Enum, JSON, Integer, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import TenantModel
from app.constants.enums import DocumentType
from datetime import datetime
from typing import Optional


class DocumentTemplate(TenantModel):
    __tablename__ = "document_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    required_fields: Mapped[list] = mapped_column(JSON, nullable=True)
    mime_types: Mapped[list] = mapped_column(JSON, nullable=True)
    max_size_kb: Mapped[int] = mapped_column(Integer, default=5120, nullable=False)
    is_required: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        Index("ix_document_templates_tenant_code", "tenant_id", "code"),
        Index("ix_document_templates_type", "template_type"),
    )


class DocumentUpload(TenantModel):
    __tablename__ = "document_uploads"

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[str] = mapped_column(
        Enum(DocumentType, name="document_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validation_status: Mapped[str] = mapped_column(
        Enum("pending", "valid", "invalid", name="document_validation_status_enum"),
        default="pending",
        nullable=False,
    )
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_document_uploads_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_document_uploads_type", "tenant_id", "document_type"),
        Index("ix_document_uploads_uploaded_by", "uploaded_by"),
        Index("ix_document_uploads_validation", "validation_status"),
    )
