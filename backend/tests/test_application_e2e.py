import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.models.product import Quote, Plan, Product
from app.models.application import Application
from app.constants.enums import ProductStatus, PlanType, QuoteStatus, ApplicationStatus


def test_create_and_submit_application_happy_path(client: TestClient, admin_headers, tenant, db):
    """Test complete flow: Quote → Application → Submit"""
    # Create product and plan
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Health Plan",
        code="HP001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    plan = Plan(
        id="plan-001",
        tenant_id=tenant.id,
        product_id="prod-001",
        name="Gold Plan",
        code="GOLD001",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=True,
    )
    db.add(plan)
    db.commit()

    # Create quote
    quote = Quote(
        id="quote-001",
        tenant_id=tenant.id,
        quote_number="QT-001",
        product_id="prod-001",
        plan_id="plan-001",
        created_by="user-001",
        customer_email="customer@test.com",
        customer_name="John Doe",
        total_premium=Decimal("500.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.commit()

    # Create application from quote
    resp = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "John Doe",
            "member_count": 1,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    app_data = resp.json()["data"]
    assert app_data["status"] == "draft"
    assert app_data["quote_id"] == "quote-001"
    app_id = app_data["id"]

    # Get application
    resp = client.get(f"/api/v1/applications/{app_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "draft"

    # Submit application
    resp = client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    app_data = resp.json()["data"]
    assert app_data["status"] == "submitted"

    # Verify quote status changed to CONVERTED
    db.refresh(quote)
    assert quote.status == QuoteStatus.CONVERTED


def test_cannot_use_same_quote_twice(client: TestClient, admin_headers, tenant, db):
    """Test that same quote cannot be used for multiple applications"""
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Health Plan",
        code="HP001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    plan = Plan(
        id="plan-001",
        tenant_id=tenant.id,
        product_id="prod-001",
        name="Gold Plan",
        code="GOLD001",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=True,
    )
    db.add(plan)
    db.flush()

    quote = Quote(
        id="quote-001",
        tenant_id=tenant.id,
        quote_number="QT-001",
        product_id="prod-001",
        plan_id="plan-001",
        created_by="user-001",
        customer_email="customer@test.com",
        customer_name="John Doe",
        total_premium=Decimal("500.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.flush()

    # Create first application
    resp1 = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "John Doe",
        },
        headers=admin_headers,
    )
    assert resp1.status_code == 201

    # Try to create second application with same quote
    resp2 = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "Jane Doe",
        },
        headers=admin_headers,
    )
    assert resp2.status_code == 400


def test_application_items_management(client: TestClient, admin_headers, tenant, db):
    """Test adding and removing application items"""
    from app.models.product import Coverage
    from app.constants.enums import CoverageType

    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Health Plan",
        code="HP001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    plan = Plan(
        id="plan-001",
        tenant_id=tenant.id,
        product_id="prod-001",
        name="Gold Plan",
        code="GOLD001",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=True,
    )
    db.add(plan)
    db.flush()

    coverage = Coverage(
        id="cov-001",
        tenant_id=tenant.id,
        plan_id="plan-001",
        name="Hospitalization",
        coverage_type=CoverageType.HOSPITALIZATION,
    )
    db.add(coverage)
    db.commit()

    quote = Quote(
        id="quote-001",
        tenant_id=tenant.id,
        quote_number="QT-001",
        product_id="prod-001",
        plan_id="plan-001",
        created_by="user-001",
        customer_email="customer@test.com",
        customer_name="John Doe",
        total_premium=Decimal("500.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.flush()

    # Create application
    resp = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "John Doe",
        },
        headers=admin_headers,
    )
    app_id = resp.json()["data"]["id"]

    # Add item
    resp = client.post(
        f"/api/v1/applications/{app_id}/items",
        json={"coverage_id": "cov-001", "premium": "100.00"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    item_id = resp.json()["data"]["id"]

    # List items
    resp = client.get(f"/api/v1/applications/{app_id}/items", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1

    # Delete item
    resp = client.delete(f"/api/v1/applications/{app_id}/items/{item_id}", headers=admin_headers)
    assert resp.status_code == 204

    # Verify item deleted
    resp = client.get(f"/api/v1/applications/{app_id}/items", headers=admin_headers)
    items = resp.json()["data"]
    assert len(items) == 0


def test_underwriting_approval_flow(client: TestClient, admin_headers, tenant, db):
    """Test application approval by underwriter"""
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Health Plan",
        code="HP001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    plan = Plan(
        id="plan-001",
        tenant_id=tenant.id,
        product_id="prod-001",
        name="Gold Plan",
        code="GOLD001",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=True,
    )
    db.add(plan)
    db.flush()

    quote = Quote(
        id="quote-001",
        tenant_id=tenant.id,
        quote_number="QT-001",
        product_id="prod-001",
        plan_id="plan-001",
        created_by="user-001",
        customer_email="customer@test.com",
        customer_name="John Doe",
        total_premium=Decimal("500.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.flush()

    # Create and submit application
    resp = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "John Doe",
        },
        headers=admin_headers,
    )
    app_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/applications/{app_id}/submit", json={}, headers=admin_headers)

    # Approve application
    resp = client.post(f"/api/v1/applications/{app_id}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "approved"


def test_underwriting_rejection_flow(client: TestClient, admin_headers, tenant, db):
    """Test application rejection by underwriter"""
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Health Plan",
        code="HP001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    plan = Plan(
        id="plan-001",
        tenant_id=tenant.id,
        product_id="prod-001",
        name="Gold Plan",
        code="GOLD001",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=True,
    )
    db.add(plan)
    db.flush()

    quote = Quote(
        id="quote-001",
        tenant_id=tenant.id,
        quote_number="QT-001",
        product_id="prod-001",
        plan_id="plan-001",
        created_by="user-001",
        customer_email="customer@test.com",
        customer_name="John Doe",
        total_premium=Decimal("500.00"),
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(quote)
    db.flush()

    # Create and submit application
    resp = client.post(
        "/api/v1/applications",
        json={
            "quote_id": "quote-001",
            "product_id": "prod-001",
            "plan_id": "plan-001",
            "customer_email": "customer@test.com",
            "customer_name": "John Doe",
        },
        headers=admin_headers,
    )
    app_id = resp.json()["data"]["id"]

    client.post(f"/api/v1/applications/{app_id}/submit", json={}, headers=admin_headers)

    # Reject application
    resp = client.post(
        f"/api/v1/applications/{app_id}/reject",
        params={"reason": "Failed medical underwriting"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "rejected"


def test_workflow_state_transitions(client: TestClient, admin_headers, tenant, db):
    """Test workflow state machine transitions"""
    # Create workflow definition
    resp = client.post(
        "/api/v1/workflows/definitions",
        json={
            "name": "Application Underwriting",
            "workflow_type": "application_underwriting",
            "description": "Underwriting workflow for applications",
            "states": ["submitted", "under_review", "approved", "rejected"],
            "transitions": [
                {
                    "from_state": "submitted",
                    "to_state": "under_review",
                    "action": "start_review",
                },
                {
                    "from_state": "under_review",
                    "to_state": "approved",
                    "action": "approve",
                },
                {
                    "from_state": "under_review",
                    "to_state": "rejected",
                    "action": "reject",
                },
            ],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    definition_id = resp.json()["data"]["id"]

    # Create workflow instance
    resp = client.post(
        "/api/v1/workflows/instances",
        json={
            "workflow_definition_id": definition_id,
            "reference_type": "application",
            "reference_id": "app-001",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    instance = resp.json()["data"]
    assert instance["current_state"] == "submitted"
    instance_id = instance["id"]

    # Transition state
    resp = client.post(
        f"/api/v1/workflows/instances/{instance_id}/transition",
        json={"action": "start_review"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["current_state"] == "under_review"

    # Transition to approval
    resp = client.post(
        f"/api/v1/workflows/instances/{instance_id}/transition",
        json={"action": "approve"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["current_state"] == "approved"
