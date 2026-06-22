from sqlalchemy import String, JSON, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TenantModel


class MarketConfig(TenantModel):
    """Per-tenant configurable key-value store for business rules.

    All market-specific values (VAT rate, PSP fee, AML thresholds, etc.)
    live here rather than in code. Query by key; value is JSON to support
    scalars, lists, and nested objects without schema changes.
    """
    __tablename__ = "market_configs"

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_market_configs_tenant_id", "tenant_id"),
        UniqueConstraint("tenant_id", "key", name="uq_market_configs_tenant_key"),
    )
