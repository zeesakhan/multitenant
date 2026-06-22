"""AML, government verification, and STR models."""
from sqlalchemy import String, Numeric, JSON, Text, Boolean, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TenantModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class PremiumLoading(TenantModel):
    """Per-member premium loadings applied by underwriters."""
    __tablename__ = "premium_loadings"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=True)
    loading_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    applied_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    application = relationship("Application", back_populates="loadings")

    __table_args__ = (
        Index("ix_premium_loadings_application_id", "application_id"),
        Index("ix_premium_loadings_tenant_id", "tenant_id"),
    )


class CommissionConfig(TenantModel):
    """Configurable commission rates per broker and plan."""
    __tablename__ = "commission_configs"

    broker_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[Optional[str]] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    insurer_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("5.00"))
    broker_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("15.50"))
    tpa_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        Index("ix_commission_configs_tenant_id", "tenant_id"),
        Index("ix_commission_configs_broker_id", "broker_id"),
        Index("ix_commission_configs_plan_id", "plan_id"),
    )


class AmlRecord(TenantModel):
    """AML check results (PEP, sanctions, risk scoring, transaction monitoring)."""
    __tablename__ = "aml_records"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    check_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cleared_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clearance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="aml_records")

    __table_args__ = (
        Index("ix_aml_records_tenant_id", "tenant_id"),
        Index("ix_aml_records_application_id", "application_id"),
        Index("ix_aml_records_status", "status"),
    )


class GovtVerificationRecord(TenantModel):
    """Government API verification results (ICP, DHA, OFAC, UN, UAE Cabinet 74)."""
    __tablename__ = "govt_verification_records"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    check_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    request_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    overridden_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    override_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="govt_checks")

    __table_args__ = (
        Index("ix_govt_verification_tenant_id", "tenant_id"),
        Index("ix_govt_verification_application_id", "application_id"),
        Index("ix_govt_verification_status", "status"),
        Index("ix_govt_verification_check_type", "check_type"),
    )


class StrRecord(TenantModel):
    """Suspicious Transaction Reports (STR) per CBUAE Notice 2021/6."""
    __tablename__ = "str_records"

    str_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    application_id: Mapped[Optional[str]] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    nature_of_suspicion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    transaction_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    approver_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    audit_trail: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_str_records_tenant_id", "tenant_id"),
        Index("ix_str_records_application_id", "application_id"),
        Index("ix_str_records_status", "status"),
        UniqueConstraint("str_reference", name="uq_str_records_reference"),
    )


class NotificationRecord(TenantModel):
    """In-portal notification records for the notification bell."""
    __tablename__ = "notification_records"

    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_notification_records_tenant_id", "tenant_id"),
        Index("ix_notification_records_recipient_user_id", "recipient_user_id"),
        Index("ix_notification_records_is_read", "is_read"),
        Index("ix_notification_records_created_at", "created_at"),
    )
