from sqlalchemy import Column, String, Enum, JSON, Boolean, Text, UniqueConstraint, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import SystemModel, Base
from app.constants.enums import TenantStatus
from datetime import datetime, timezone
from typing import Optional


class Tenant(SystemModel):
    __tablename__ = "tenants"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(TenantStatus, name="tenant_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    brand_config = relationship("BrandConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class BrandConfig(Base):
    __tablename__ = "brand_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), default="#1976D2", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#424242", nullable=False)
    accent_color: Mapped[str] = mapped_column(String(20), default="#FF5722", nullable=False)
    font_family: Mapped[str] = mapped_column(String(100), default="Inter", nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", back_populates="brand_config")
