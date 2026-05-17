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


def test_create_claim(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    resp = client.post("/api/v1/claims", json={
        "policy_id": policy.id,
        "claim_type": "outpatient",
        "incident_date": "2026-05-01",
        "description": "Routine doctor visit for checkup",
        "claimed_amount": 300.0,
    }, headers=admin_headers)
    assert resp.status_code == 201
    claim = resp.json()["data"]
    assert claim["status"] == "submitted"
    assert claim["claim_number"].startswith("CLM-")


def test_claim_workflow(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    resp = client.post("/api/v1/claims", json={
        "policy_id": policy.id,
        "claim_type": "hospitalization",
        "incident_date": "2026-04-15",
        "description": "Emergency hospitalization for appendectomy",
        "claimed_amount": 5000.0,
    }, headers=admin_headers)
    claim_id = resp.json()["data"]["id"]

    # Start review
    resp = client.post(f"/api/v1/claims/{claim_id}/review", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "under_review"

    # Approve
    resp = client.post(f"/api/v1/claims/{claim_id}/approve",
                       json={"approved_amount": 4500.0}, headers=admin_headers)
    assert resp.status_code == 200
    claim = resp.json()["data"]
    assert claim["status"] == "approved"
    assert float(claim["approved_amount"]) == 4500.0

    # Pay
    resp = client.post(f"/api/v1/claims/{claim_id}/pay", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "paid"


def test_reject_claim(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    resp = client.post("/api/v1/claims", json={
        "policy_id": policy.id,
        "claim_type": "dental",
        "incident_date": "2026-05-10",
        "description": "Cosmetic dental procedure not covered",
        "claimed_amount": 800.0,
    }, headers=admin_headers)
    claim_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/claims/{claim_id}/review", headers=admin_headers)

    resp = client.post(f"/api/v1/claims/{claim_id}/reject",
                       json={"reason": "Cosmetic procedures are excluded"}, headers=admin_headers)
    assert resp.status_code == 200
    claim = resp.json()["data"]
    assert claim["status"] == "rejected"
    assert "Cosmetic" in claim["rejection_reason"]


def test_list_claims(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)

    for i in range(4):
        client.post("/api/v1/claims", json={
            "policy_id": policy.id,
            "claim_type": "pharmacy",
            "incident_date": "2026-05-01",
            "description": f"Pharmacy claim number {i} with enough detail",
            "claimed_amount": 50.0 * (i + 1),
        }, headers=admin_headers)

    resp = client.get("/api/v1/claims", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 4


def test_cannot_claim_on_inactive_policy(client: TestClient, admin_headers, admin_user, tenant, db):
    policy = _make_policy(db, tenant.id, admin_user.id)
    policy.status = PolicyStatus.CANCELLED
    db.flush()

    resp = client.post("/api/v1/claims", json={
        "policy_id": policy.id,
        "claim_type": "outpatient",
        "incident_date": "2026-05-01",
        "description": "This should not be allowed on cancelled policy",
        "claimed_amount": 100.0,
    }, headers=admin_headers)
    assert resp.status_code == 400


def test_tenant_isolation_claims(client: TestClient, admin_headers, admin_user, tenant, tenant2, db):
    from tests.conftest import create_access_token
    from app.models.user import User
    from app.constants.enums import UserType, UserStatus
    from passlib.context import CryptContext

    policy = _make_policy(db, tenant.id, admin_user.id)
    resp = client.post("/api/v1/claims", json={
        "policy_id": policy.id,
        "claim_type": "outpatient",
        "incident_date": "2026-05-01",
        "description": "Cross-tenant isolation test claim for tenant one",
        "claimed_amount": 200.0,
    }, headers=admin_headers)
    assert resp.status_code == 201

    # User from tenant2 should see 0 claims
    crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user2 = User(
        id=str(uuid.uuid4()), tenant_id=tenant2.id, email="admin2@other.com",
        password_hash=crypt.hash("pass"), first_name="A", last_name="B",
        user_type=UserType.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db.add(user2)
    db.flush()
    token2 = create_access_token({
        "sub": user2.id, "tenant_id": tenant2.id,
        "email": user2.email, "user_type": user2.user_type,
    })
    headers2 = {"Authorization": f"Bearer {token2}", "X-Tenant-ID": tenant2.id}
    resp2 = client.get("/api/v1/claims", headers=headers2)
    assert resp2.json()["pagination"]["total"] == 0
