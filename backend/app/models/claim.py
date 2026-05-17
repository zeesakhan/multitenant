from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from app.models.base import TenantModel
from app.constants.enums import ClaimStatus, ClaimType
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


class Claim(TenantModel):
    __tablename__ = "claims"

    claim_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)
    member_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    claim_type: Mapped[str] = mapped_column(Enum(ClaimType, name="claim_type_enum"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(ClaimStatus, name="claim_status_enum"),
        default=ClaimStatus.SUBMITTED,
        nullable=False,
    )
    incident_date: Mapped[date] = mapped_column(DateTime, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    policy = sa_relationship("Policy", back_populates="claims")

    __table_args__ = (
        Index("ix_claims_policy", "policy_id"),
        Index("ix_claims_tenant_status", "tenant_id", "status"),
    )
