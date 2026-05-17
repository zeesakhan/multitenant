import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from app.models.product import Product, Plan, Quote
from app.constants.enums import ProductStatus, PlanType, QuoteStatus


def _make_product_and_plan(db, tenant_id: str):
    product = Product(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        name="Health Basic", code=f"HB_{uuid.uuid4().hex[:4].upper()}",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()
    plan = Plan(
        id=str(uuid.uuid4()), tenant_id=tenant_id, product_id=product.id,
        name="Individual", code=f"IND_{uuid.uuid4().hex[:4].upper()}",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
    )
    db.add(plan)
    db.flush()
    return product, plan


def _create_quote(client, headers, product_id, plan_id):
    return client.post("/api/v1/quotations", json={
        "product_id": product_id,
        "plan_id": plan_id,
        "customer_name": f"Customer {uuid.uuid4().hex[:4]}",
        "customer_email": f"customer_{uuid.uuid4().hex[:6]}@example.com",
    }, headers=headers)


def test_create_quote(client: TestClient, auth_headers, tenant, db):
    product, plan = _make_product_and_plan(db, tenant.id)
    resp = _create_quote(client, auth_headers, product.id, plan.id)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "quote_number" in data
    assert data["total_premium"] is not None


def test_list_quotes(client: TestClient, auth_headers, tenant, db):
    product, plan = _make_product_and_plan(db, tenant.id)
    _create_quote(client, auth_headers, product.id, plan.id)
    resp = client.get("/api/v1/quotations", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


def test_get_quote(client: TestClient, auth_headers, tenant, db):
    product, plan = _make_product_and_plan(db, tenant.id)
    create_resp = _create_quote(client, auth_headers, product.id, plan.id)
    quote_id = create_resp.json()["data"]["id"]
    resp = client.get(f"/api/v1/quotations/{quote_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == quote_id


def test_quote_not_found(client: TestClient, auth_headers):
    resp = client.get(f"/api/v1/quotations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_quote_tenant_isolation(client: TestClient, auth_headers, tenant2, db):
    product2, plan2 = _make_product_and_plan(db, tenant2.id)
    from datetime import datetime, timezone, timedelta
    q = Quote(
        id=str(uuid.uuid4()), tenant_id=tenant2.id,
        quote_number=f"Q-{uuid.uuid4().hex[:6].upper()}",
        customer_name="Foreign Customer", customer_email="foreign@test.com",
        product_id=product2.id, plan_id=plan2.id,
        total_premium=Decimal("100.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(q)
    db.flush()
    resp = client.get(f"/api/v1/quotations/{q.id}", headers=auth_headers)
    assert resp.status_code == 404


def test_send_quote(client: TestClient, auth_headers, tenant, db):
    product, plan = _make_product_and_plan(db, tenant.id)
    create_resp = _create_quote(client, auth_headers, product.id, plan.id)
    quote_id = create_resp.json()["data"]["id"]
    resp = client.post(f"/api/v1/quotations/{quote_id}/send", json={}, headers=auth_headers)
    assert resp.status_code == 200


def test_list_quotes_requires_auth(client: TestClient):
    resp = client.get("/api/v1/quotations")
    assert resp.status_code in (401, 403)
