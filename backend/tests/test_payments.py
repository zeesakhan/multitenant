import pytest
import uuid
from fastapi.testclient import TestClient
from app.models.product import Product, Plan
from app.models.policy import Policy
from app.constants.enums import ProductStatus, PlanType, PolicyStatus
from decimal import Decimal
from datetime import datetime, timezone, timedelta


def _make_policy(db, tenant_id: str, user_id: str) -> Policy:
    product = Product(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        name="Health", code=f"H_{uuid.uuid4().hex[:4].upper()}",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()
    plan = Plan(
        id=str(uuid.uuid4()), tenant_id=tenant_id, product_id=product.id,
        name="Ind", code="IND", plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("400.00"),
    )
    db.add(plan)
    db.flush()
    now = datetime.now(timezone.utc)
    policy = Policy(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        policy_number=f"POL-{uuid.uuid4().hex[:6].upper()}",
        product_id=product.id, plan_id=plan.id,
        customer_name="Test Customer", customer_email="test@example.com",
        total_premium=Decimal("400.00"), member_count=1,
        status=PolicyStatus.ACTIVE,
        effective_date=now, expiry_date=now + timedelta(days=365),
        issued_by=user_id, issued_at=now,
    )
    db.add(policy)
    db.flush()
    return policy


def test_record_payment(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    resp = client.post(
        f"/api/v1/policies/{policy.id}/payments",
        json={"amount": 400.0, "method": "bank_transfer", "reference": "TXN001"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    payment = resp.json()["data"]
    assert payment["payment_number"].startswith("PAY-")
    assert float(payment["amount"]) == 400.0
    assert payment["status"] == "success"


def test_list_payments_by_policy(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    for i in range(3):
        client.post(
            f"/api/v1/policies/{policy.id}/payments",
            json={"amount": 100.0 * (i + 1), "method": "card"},
            headers=admin_headers,
        )

    resp = client.get(f"/api/v1/policies/{policy.id}/payments", headers=admin_headers)
    assert resp.status_code == 200
    payments = resp.json()["data"]
    assert len(payments) == 3


def test_list_all_payments(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)
    client.post(
        f"/api/v1/policies/{policy.id}/payments",
        json={"amount": 250.0, "method": "upi"},
        headers=admin_headers,
    )

    resp = client.get("/api/v1/payments", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


def test_cannot_pay_renewed_policy(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)
    policy.status = "renewed"
    db.flush()

    resp = client.post(
        f"/api/v1/policies/{policy.id}/payments",
        json={"amount": 100.0, "method": "cash"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_payment_requires_valid_policy(client: TestClient, admin_headers, tenant, db):
    resp = client.post(
        "/api/v1/policies/nonexistent-id/payments",
        json={"amount": 100.0, "method": "card"},
        headers=admin_headers,
    )
    assert resp.status_code in (400, 404)
