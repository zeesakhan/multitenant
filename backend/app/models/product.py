from sqlalchemy import Column, String, Enum, JSON, Numeric, Boolean, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import TenantModel
from app.constants.enums import ProductStatus, PlanType, CoverageType
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal


class Product(TenantModel):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ProductStatus, name="product_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=ProductStatus.DRAFT,
        nullable=False,
    )
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    plans = relationship("Plan", back_populates="product", cascade="all, delete-orphan")
    rate_cards = relationship("RateCard", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_products_tenant_code"),
        Index("ix_products_tenant_status", "tenant_id", "status"),
    )


class Plan(TenantModel):
    __tablename__ = "plans"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_type: Mapped[str] = mapped_column(
        Enum(PlanType, name="plan_type_enum", values_callable=lambda x: [e.value for e in x]),
        default=PlanType.INDIVIDUAL,
        nullable=False,
    )
    base_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    coverage_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    included_services: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    exclusions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product = relationship("Product", back_populates="plans")
    coverages = relationship("Coverage", back_populates="plan", cascade="all, delete-orphan")
    rate_cards = relationship("RateCard", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "code", name="uq_plans_tenant_product_code"),
        Index("ix_plans_product", "product_id"),
    )


class Coverage(TenantModel):
    __tablename__ = "coverages"

    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    coverage_type: Mapped[str] = mapped_column(
        Enum(CoverageType, name="coverage_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    limit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    copay: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    coinsurance_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    plan = relationship("Plan", back_populates="coverages")

    __table_args__ = (
        Index("ix_coverages_plan", "plan_id"),
    )


class RateCard(TenantModel):
    __tablename__ = "rate_cards"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rates: Mapped[dict] = mapped_column(JSON, nullable=False)

    product = relationship("Product", back_populates="rate_cards")
    plan = relationship("Plan", back_populates="rate_cards")

    __table_args__ = (
        Index("ix_rate_cards_product", "product_id"),
        Index("ix_rate_cards_plan", "plan_id"),
        Index("ix_rate_cards_effective", "tenant_id", "effective_date", "expiry_date"),
    )


class Quote(TenantModel):
    __tablename__ = "quotes"

    quote_number: Mapped[str] = mapped_column(String(100), nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("draft", "sent", "viewed", "expired", "converted", "declined", name="quote_status_enum"),
        default="draft",
        nullable=False,
    )
    breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "quote_number", name="uq_quotes_tenant_number"),
        Index("ix_quotes_tenant_status", "tenant_id", "status"),
        Index("ix_quotes_created_by", "created_by"),
        Index("ix_quotes_valid_until", "valid_until"),
    )
