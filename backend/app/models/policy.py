from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TenantModel
from app.constants.enums import PolicyStatus
from datetime import datetime
from typing import Optional
from decimal import Decimal


class Policy(TenantModel):
    __tablename__ = "policies"

    policy_number: Mapped[str] = mapped_column(String(100), nullable=False)
    application_id: Mapped[Optional[str]] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    quote_id: Mapped[Optional[str]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(nullable=False, default=1)
    total_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PolicyStatus, name="policy_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=PolicyStatus.ACTIVE,
        nullable=False,
    )
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    product = relationship("Product")
    plan = relationship("Plan")
    payments = relationship("Payment", back_populates="policy", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="policy", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_number", name="uq_policies_tenant_number"),
        # Removed unique constraint on application_id to allow renewals
        Index("ix_policies_tenant_status", "tenant_id", "status"),
        Index("ix_policies_customer_email", "tenant_id", "customer_email"),
    )
