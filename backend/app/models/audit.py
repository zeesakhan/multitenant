from sqlalchemy import Column, String, Enum, JSON, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from app.constants.enums import AuditAction
from datetime import datetime, timezone
from typing import Optional


class AuditLog(Base):
    """Immutable audit trail. Never updated, only inserted."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(
        Enum(AuditAction, name="audit_action_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_logs_tenant_timestamp", "tenant_id", "timestamp"),
        Index("ix_audit_logs_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_user", "user_id", "timestamp"),
    )
