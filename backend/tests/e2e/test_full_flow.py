"""
End-to-end: Quote → Application → submit → approve → issue policy → record payment.

Uses only REST endpoints (no direct DB calls after setup) to validate the full
production workflow as a user would experience it.
"""
import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.models.product import Product, Plan, Quote, Coverage
from app.constants.enums import ProductStatus, PlanType, QuoteStatus, CoverageType


# ── Helpers ───────────────────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())


def setup_product_and_plan(db, tenant_id: str) -> tuple[str, str, str]:
    """Create a product, plan, and coverage. Return (product_id, plan_id, coverage_id)."""
    product_id = uid()
    plan_id = uid()
    coverage_id = uid()

    product = Product(
        id=product_id,
        tenant_id=tenant_id,
        name="E2E Health Plan",
        code=f"E2E{uuid.uuid4().hex[:6].upper()}",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()

    plan = Plan(
        id=plan_id,
        tenant_id=tenant_id,
        product_id=product_id,
        name="E2E Gold",
        code=f"GLD{uuid.uuid4().hex[:6].upper()}",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("350.00"),
        is_active=True,
    )
    db.add(plan)
    db.flush()

    coverage = Coverage(
        id=coverage_id,
        tenant_id=tenant_id,
        plan_id=plan_id,
        name="Hospitalization",
        coverage_type=CoverageType.HOSPITALIZATION,
    )
    db.add(coverage)
    db.flush()

    return product_id, plan_id, coverage_id


def create_quote_in_db(db, tenant_id: str, product_id: str, plan_id: str) -> str:
    quote_id = uid()
    quote = Quote(
        id=quote_id,
        tenant_id=tenant_id,
        quote_number=f"QT-E2E-{uuid.uuid4().hex[:6].upper()}",
        product_id=product_id,
        plan_id=plan_id,
        created_by=uid(),
        customer_email="e2e.customer@example.com",
        customer_name="E2E Customer",
        total_premium=Decimal("350.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.flush()
    return quote_id


# ── Full-flow test ────────────────────────────────────────────────────────────

def test_full_flow_quote_to_payment(client, admin_headers, tenant, db):
    """
    Full happy-path:
      1. Seed product / plan / coverage
      2. Seed a quote
      3. Create application from quote  → status: draft
      4. Add coverage item              → item created
      5. Submit application             → status: submitted
      6. Approve application            → status: approved
      7. Issue policy                   → status: issued, policy created
      8. Record payment on policy       → payment recorded
    """
    # ── Step 1 & 2: setup ─────────────────────────────────────────────────────
    product_id, plan_id, coverage_id = setup_product_and_plan(db, tenant.id)
    quote_id = create_quote_in_db(db, tenant.id, product_id, plan_id)

    # ── Step 3: create application ─────────────────────────────────────────────
    res = client.post(
        "/api/v1/applications",
        json={
            "quote_id": quote_id,
            "product_id": product_id,
            "plan_id": plan_id,
            "customer_name": "E2E Customer",
            "customer_email": "e2e.customer@example.com",
            "member_count": 1,
        },
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    app_data = res.json()["data"]
    app_id = app_data["id"]
    assert app_data["status"] == "draft"

    # ── Step 4: add coverage item ──────────────────────────────────────────────
    res = client.post(
        f"/api/v1/applications/{app_id}/items",
        json={"coverage_id": coverage_id, "premium": "350.00"},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text

    # ── Step 5: submit ─────────────────────────────────────────────────────────
    res = client.post(f"/api/v1/applications/{app_id}/submit", json={}, headers=admin_headers)
    assert res.status_code == 200, res.text
    assert res.json()["data"]["status"] == "submitted"

    # ── Step 6: approve ────────────────────────────────────────────────────────
    res = client.post(f"/api/v1/applications/{app_id}/approve", headers=admin_headers)
    assert res.status_code == 200, res.text
    assert res.json()["data"]["status"] == "approved"

    # ── Step 7: issue policy ───────────────────────────────────────────────────
    res = client.post(f"/api/v1/applications/{app_id}/issue", headers=admin_headers)
    assert res.status_code in (200, 201), res.text
    issue_data = res.json()["data"]
    # The endpoint may return the policy directly or the updated application
    if "policy_number" in issue_data:
        # Returned the policy object
        policy_id = issue_data["id"]
        assert issue_data["status"] in ("active", "issued")
    else:
        # Returned the application; fetch policy separately
        assert issue_data["status"] == "issued"
        res = client.get("/api/v1/policies", headers=admin_headers)
        assert res.status_code == 200
        policies = res.json()["data"]
        policy = next((p for p in policies if p.get("application_id") == app_id), None)
        assert policy is not None, "Policy was not created after issuing application"
        policy_id = policy["id"]
        assert policy["status"] in ("active", "issued")

    # ── Step 8: record payment ─────────────────────────────────────────────────
    res = client.post(
        f"/api/v1/policies/{policy_id}/payments",
        json={
            "amount": 350.00,
            "method": "bank_transfer",
            "reference": "E2E-REF-001",
            "notes": "E2E test payment",
        },
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    payment = res.json()["data"]
    assert float(payment["amount"]) == 350.00
    assert payment["method"] == "bank_transfer"
