from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from app.models.base import TenantModel
from app.constants.enums import PaymentStatus, PaymentMethod
from datetime import datetime
from typing import Optional
from decimal import Decimal


class Payment(TenantModel):
    __tablename__ = "payments"

    payment_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.SUCCESS,
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"),
        default=PaymentMethod.BANK_TRANSFER,
        nullable=False,
    )
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    policy = sa_relationship("Policy", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_policy", "policy_id"),
        Index("ix_payments_tenant_status", "tenant_id", "status"),
    )
