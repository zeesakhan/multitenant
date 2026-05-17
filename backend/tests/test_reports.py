import pytest
import uuid
from fastapi.testclient import TestClient
from app.models.product import Product, Plan
from app.models.policy import Policy
from app.models.payment import Payment
from app.models.claim import Claim
from app.models.application import Application
from app.constants.enums import (
    ProductStatus, PlanType, PolicyStatus, PaymentStatus, PaymentMethod,
    ClaimStatus, ClaimType, ApplicationStatus,
)
from decimal import Decimal
from datetime import datetime, timezone, timedelta


def _seed_report_data(db, tenant_id: str, user_id: str) -> dict:
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
        base_premium=Decimal("500.00"),
    )
    db.add(plan)
    db.flush()

    now = datetime.now(timezone.utc)

    app = Application(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        application_number=f"AP-{uuid.uuid4().hex[:6].upper()}",
        customer_name="Report User", customer_email="report@test.com",
        product_id=product.id, plan_id=plan.id,
        total_premium=Decimal("500.00"), member_count=1,
        status=ApplicationStatus.APPROVED, created_by=user_id,
    )
    db.add(app)
    db.flush()

    policy = Policy(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        policy_number=f"POL-{uuid.uuid4().hex[:6].upper()}",
        product_id=product.id, plan_id=plan.id,
        customer_name="Report User", customer_email="report@test.com",
        total_premium=Decimal("500.00"), member_count=1,
        status=PolicyStatus.ACTIVE,
        effective_date=now, expiry_date=now + timedelta(days=365),
        issued_by=user_id, issued_at=now,
    )
    db.add(policy)
    db.flush()

    payment = Payment(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        payment_number=f"PAY-{uuid.uuid4().hex[:6].upper()}",
        policy_id=policy.id,
        amount=Decimal("500.00"),
        status=PaymentStatus.SUCCESS,
        method=PaymentMethod.BANK_TRANSFER,
        paid_at=now,
    )
    db.add(payment)

    claim = Claim(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        claim_number=f"CLM-{uuid.uuid4().hex[:6].upper()}",
        policy_id=policy.id,
        claim_type=ClaimType.OUTPATIENT,
        status=ClaimStatus.SUBMITTED,
        incident_date=now,
        description="Test claim for reporting",
        claimed_amount=Decimal("200.00"),
    )
    db.add(claim)
    db.flush()

    return {"policy": policy, "payment": payment, "claim": claim, "app": app}


def test_reports_summary(client: TestClient, admin_headers, admin_user, tenant, db):
    _seed_report_data(db, tenant.id, admin_user.id)

    resp = client.get("/api/v1/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    summary = resp.json()["data"]
    assert summary["active_policies"] >= 1
    assert summary["open_claims"] >= 1
    assert summary["monthly_premium_due"] > 0
    assert summary["collected_this_month"] >= 0
    assert "expiring_soon_30d" in summary
    assert "pending_applications" in summary


def test_reports_applications_by_month(client: TestClient, admin_headers, admin_user, tenant, db):
    _seed_report_data(db, tenant.id, admin_user.id)

    resp = client.get("/api/v1/reports/applications?months=6", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert isinstance(rows, list)
    if rows:
        assert "month" in rows[0]
        assert "total" in rows[0]


def test_reports_premium_by_month(client: TestClient, admin_headers, admin_user, tenant, db):
    _seed_report_data(db, tenant.id, admin_user.id)

    resp = client.get("/api/v1/reports/premium?months=6", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert isinstance(rows, list)
    if rows:
        assert "month" in rows[0]
        assert "collected" in rows[0]


def test_reports_claims_by_month(client: TestClient, admin_headers, admin_user, tenant, db):
    _seed_report_data(db, tenant.id, admin_user.id)

    resp = client.get("/api/v1/reports/claims?months=6", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert isinstance(rows, list)
    if rows:
        assert "month" in rows[0]
        assert "total" in rows[0]


def test_dashboard_stats(client: TestClient, admin_headers, admin_user, tenant, db):
    _seed_report_data(db, tenant.id, admin_user.id)

    resp = client.get("/api/v1/dashboard/stats", headers=admin_headers)
    assert resp.status_code == 200
    stats = resp.json()["data"]
    assert "policies" in stats
    assert "applications" in stats
    assert stats["policies"]["total"] >= 1
