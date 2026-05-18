"""
Test object factories. Return model instances without committing to the DB.
Usage in tests:
    from tests.fixtures.factories import make_product, make_plan
    product = make_product(tenant.id)
    db.add(product); db.flush()
"""
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.models.product import Product, Plan, Quote
from app.models.application import Application
from app.constants.enums import (
    ProductStatus, PlanType, QuoteStatus, ApplicationStatus,
)


def make_product(tenant_id: str, **kwargs) -> Product:
    return Product(
        id=kwargs.pop("id", str(uuid.uuid4())),
        tenant_id=tenant_id,
        name=kwargs.pop("name", "Test Product"),
        code=kwargs.pop("code", f"PROD-{uuid.uuid4().hex[:6].upper()}"),
        status=kwargs.pop("status", ProductStatus.ACTIVE),
        **kwargs,
    )


def make_plan(tenant_id: str, product_id: str, **kwargs) -> Plan:
    return Plan(
        id=kwargs.pop("id", str(uuid.uuid4())),
        tenant_id=tenant_id,
        product_id=product_id,
        name=kwargs.pop("name", "Test Plan"),
        code=kwargs.pop("code", f"PLAN-{uuid.uuid4().hex[:6].upper()}"),
        plan_type=kwargs.pop("plan_type", PlanType.INDIVIDUAL),
        base_premium=kwargs.pop("base_premium", Decimal("299.00")),
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )


def make_quote(tenant_id: str, product_id: str, plan_id: str, **kwargs) -> Quote:
    return Quote(
        id=kwargs.pop("id", str(uuid.uuid4())),
        tenant_id=tenant_id,
        quote_number=kwargs.pop("quote_number", f"QT-{uuid.uuid4().hex[:8].upper()}"),
        product_id=product_id,
        plan_id=plan_id,
        created_by=kwargs.pop("created_by", str(uuid.uuid4())),
        customer_name=kwargs.pop("customer_name", "Test Customer"),
        customer_email=kwargs.pop("customer_email", "customer@test.com"),
        total_premium=kwargs.pop("total_premium", Decimal("299.00")),
        status=kwargs.pop("status", QuoteStatus.DRAFT),
        valid_until=kwargs.pop("valid_until", datetime.now(timezone.utc) + timedelta(days=30)),
        **kwargs,
    )


def make_application(tenant_id: str, **kwargs) -> Application:
    return Application(
        id=kwargs.pop("id", str(uuid.uuid4())),
        tenant_id=tenant_id,
        application_number=kwargs.pop("application_number", f"APP-{uuid.uuid4().hex[:8].upper()}"),
        customer_name=kwargs.pop("customer_name", "Test Customer"),
        customer_email=kwargs.pop("customer_email", "customer@test.com"),
        member_count=kwargs.pop("member_count", 1),
        total_premium=kwargs.pop("total_premium", Decimal("299.00")),
        status=kwargs.pop("status", ApplicationStatus.DRAFT),
        **kwargs,
    )
