from sqlalchemy import Column, String, Enum, JSON, Numeric, Boolean, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import TenantModel
from app.constants.enums import ApplicationStatus
from datetime import datetime
from typing import Optional
from decimal import Decimal


class Application(TenantModel):
    __tablename__ = "applications"

    application_number: Mapped[str] = mapped_column(String(100), nullable=False)
    quote_id: Mapped[Optional[str]] = mapped_column(ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[Optional[str]] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(nullable=False, default=1)
    total_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.DRAFT,
        nullable=False,
    )
    breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    additional_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    items = relationship("ApplicationItem", back_populates="application", cascade="all, delete-orphan")
    members = relationship("Member", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "application_number", name="uq_applications_tenant_number"),
        Index("ix_applications_tenant_status", "tenant_id", "status"),
        Index("ix_applications_quote_id", "quote_id"),
        Index("ix_applications_created_by", "created_by"),
    )


class ApplicationItem(TenantModel):
    __tablename__ = "application_items"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    coverage_id: Mapped[str] = mapped_column(ForeignKey("coverages.id", ondelete="RESTRICT"), nullable=False)
    premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="application_item_status_enum"),
        default="pending",
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    application = relationship("Application", back_populates="items")
    coverage = relationship("Coverage")

    __table_args__ = (
        Index("ix_application_items_application", "application_id"),
        Index("ix_application_items_coverage", "coverage_id"),
    )
