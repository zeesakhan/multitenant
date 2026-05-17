import pytest
import uuid
from fastapi.testclient import TestClient
from app.models.product import Product, Plan
from app.models.application import Application
from app.models.policy import Policy
from app.constants.enums import (
    ProductStatus, PlanType, ApplicationStatus, PolicyStatus,
)
from decimal import Decimal
from datetime import datetime, timezone, timedelta


def _make_product(db, tenant_id: str) -> tuple:
    product = Product(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        name="Health Basic", code=f"HB_{uuid.uuid4().hex[:4].upper()}",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()
    plan = Plan(
        id=str(uuid.uuid4()), tenant_id=tenant_id, product_id=product.id,
        name="Individual", code="IND", plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
    )
    db.add(plan)
    db.flush()
    return product, plan


def _make_approved_app(db, tenant_id: str, product_id: str, plan_id: str, user_id: str) -> Application:
    app = Application(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        application_number=f"AP-{uuid.uuid4().hex[:6].upper()}",
        customer_name="Jane Doe", customer_email="jane@example.com",
        product_id=product_id, plan_id=plan_id,
        total_premium=Decimal("500.00"), member_count=1,
        status=ApplicationStatus.APPROVED, created_by=user_id,
    )
    db.add(app)
    db.flush()
    return app


def test_issue_policy(client: TestClient, admin_headers, admin_user, tenant, db):
    product, plan = _make_product(db, tenant.id)
    app = _make_approved_app(db, tenant.id, product.id, plan.id, admin_user.id)

    resp = client.post(f"/api/v1/applications/{app.id}/issue", headers=admin_headers)
    assert resp.status_code == 201
    policy = resp.json()["data"]
    assert policy["status"] == "active"
    assert policy["customer_email"] == "jane@example.com"
    assert policy["policy_number"].startswith("POL-")


def test_cannot_issue_unapproved(client: TestClient, admin_headers, admin_user, tenant, db):
    product, plan = _make_product(db, tenant.id)
    app = Application(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        application_number=f"AP-{uuid.uuid4().hex[:6].upper()}",
        customer_name="Bob", customer_email="bob@example.com",
        product_id=product.id, plan_id=plan.id,
        total_premium=Decimal("200.00"), member_count=1,
        status=ApplicationStatus.SUBMITTED, created_by=admin_user.id,
    )
    db.add(app)
    db.flush()

    resp = client.post(f"/api/v1/applications/{app.id}/issue", headers=admin_headers)
    assert resp.status_code == 400


def test_cannot_issue_twice(client: TestClient, admin_headers, admin_user, tenant, db):
    product, plan = _make_product(db, tenant.id)
    app = _make_approved_app(db, tenant.id, product.id, plan.id, admin_user.id)

    client.post(f"/api/v1/applications/{app.id}/issue", headers=admin_headers)
    resp = client.post(f"/api/v1/applications/{app.id}/issue", headers=admin_headers)
    assert resp.status_code == 400


def test_list_policies(client: TestClient, admin_headers, admin_user, tenant, db):
    product, plan = _make_product(db, tenant.id)
    now = datetime.now(timezone.utc)
    for i in range(3):
        db.add(Policy(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            policy_number=f"POL-TEST-{i}",
            product_id=product.id, plan_id=plan.id,
            customer_name=f"Customer {i}", customer_email=f"c{i}@test.com",
            total_premium=Decimal("300.00"), member_count=1,
            status=PolicyStatus.ACTIVE,
            effective_date=now, expiry_date=now + timedelta(days=365),
        ))
    db.flush()

    resp = client.get("/api/v1/policies", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 3


def test_renew_policy(client: TestClient, admin_headers, admin_user, tenant, db):
    product, plan = _make_product(db, tenant.id)
    now = datetime.now(timezone.utc)
    policy = Policy(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        policy_number="POL-RENEW-001",
        product_id=product.id, plan_id=plan.id,
        customer_name="Renew Me", customer_email="renew@test.com",
        total_premium=Decimal("500.00"), member_count=1,
        status=PolicyStatus.ACTIVE,
        effective_date=now, expiry_date=now + timedelta(days=365),
        issued_by=admin_user.id, issued_at=now,
    )
    db.add(policy)
    db.flush()

    resp = client.post(f"/api/v1/policies/{policy.id}/renew", headers=admin_headers)
    assert resp.status_code == 201
    renewed = resp.json()["data"]
    assert renewed["policy_number"] != "POL-RENEW-001"
    assert renewed["status"] == "active"
    assert renewed["application_id"] is None


def test_tenant_isolation_policies(client: TestClient, admin_headers, admin_user, tenant, tenant2, db):
    product, plan = _make_product(db, tenant.id)
    product2, plan2 = _make_product(db, tenant2.id)
    now = datetime.now(timezone.utc)

    db.add(Policy(
        id=str(uuid.uuid4()), tenant_id=tenant.id, policy_number="POL-T1-001",
        product_id=product.id, plan_id=plan.id,
        customer_name="T1 Customer", customer_email="t1@test.com",
        total_premium=Decimal("300.00"), member_count=1, status=PolicyStatus.ACTIVE,
        effective_date=now, expiry_date=now + timedelta(days=365),
    ))
    db.add(Policy(
        id=str(uuid.uuid4()), tenant_id=tenant2.id, policy_number="POL-T2-001",
        product_id=product2.id, plan_id=plan2.id,
        customer_name="T2 Customer", customer_email="t2@test.com",
        total_premium=Decimal("300.00"), member_count=1, status=PolicyStatus.ACTIVE,
        effective_date=now, expiry_date=now + timedelta(days=365),
    ))
    db.flush()

    resp = client.get("/api/v1/policies", headers=admin_headers)
    numbers = [p["policy_number"] for p in resp.json()["data"]]
    assert "POL-T1-001" in numbers
    assert "POL-T2-001" not in numbers
