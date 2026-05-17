import pytest
from fastapi.testclient import TestClient
from app.schemas.product import ProductCreate, PlanCreate, CoverageCreate
from app.constants.enums import ProductStatus, PlanType, CoverageType
from decimal import Decimal


def test_create_product(client: TestClient, admin_headers, tenant):
    resp = client.post(
        "/api/v1/products",
        json={
            "name": "Health Plus",
            "code": "HLTH001",
            "description": "Comprehensive health plan",
            "status": "draft",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Health Plus"
    assert data["code"] == "HLTH001"
    assert data["status"] == "draft"


def test_get_product(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Test Product",
        code="TEST001",
        status=ProductStatus.DRAFT,
    )
    db.add(product)
    db.flush()

    resp = client.get(f"/api/v1/products/prod-001", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == "prod-001"
    assert data["name"] == "Test Product"


def test_list_products(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product
    for i in range(3):
        product = Product(
            id=f"prod-{i}",
            tenant_id=tenant.id,
            name=f"Product {i}",
            code=f"CODE{i}",
            status=ProductStatus.ACTIVE,
        )
        db.add(product)
    db.flush()

    resp = client.get("/api/v1/products", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] >= 3


def test_update_product(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Original Name",
        code="CODE001",
        status=ProductStatus.DRAFT,
    )
    db.add(product)
    db.flush()

    resp = client.put(
        "/api/v1/products/prod-001",
        json={"name": "Updated Name", "status": "active"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Updated Name"
    assert data["status"] == "active"


def test_create_plan(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Test Product",
        code="PROD001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()

    resp = client.post(
        "/api/v1/products/prod-001/plans",
        json={
            "name": "Gold Plan",
            "code": "GOLD001",
            "plan_type": "individual",
            "base_premium": "500.00",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Gold Plan"
    assert data["plan_type"] == "individual"
    assert float(data["base_premium"]) == 500.0


def test_add_coverage_to_plan(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product, Plan
    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Test Product",
        code="PROD001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()

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

    resp = client.post(
        "/api/v1/products/prod-001/plans/plan-001/coverages",
        json={
            "name": "Hospitalization",
            "coverage_type": "hospitalization",
            "limit_amount": "500000.00",
            "copay": "2500.00",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Hospitalization"
    assert data["coverage_type"] == "hospitalization"


def test_tenant_isolation_products(client: TestClient, auth_headers, tenant, tenant2, db):
    """Verify that users can only see their tenant's products."""
    from app.models.product import Product

    product_t1 = Product(
        id="prod-t1-001",
        tenant_id=tenant.id,
        name="Tenant 1 Product",
        code="T1PROD001",
        status=ProductStatus.ACTIVE,
    )
    product_t2 = Product(
        id="prod-t2-001",
        tenant_id=tenant2.id,
        name="Tenant 2 Product",
        code="T2PROD001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product_t1)
    db.add(product_t2)
    db.flush()

    resp = client.get("/api/v1/products", headers=auth_headers)
    assert resp.status_code == 200
    products = resp.json()["data"]

    product_ids = [p["id"] for p in products]
    assert "prod-t1-001" in product_ids
    assert "prod-t2-001" not in product_ids


def test_get_plan_details(client: TestClient, admin_headers, tenant, db):
    from app.models.product import Product, Plan, Coverage

    product = Product(
        id="prod-001",
        tenant_id=tenant.id,
        name="Test Product",
        code="PROD001",
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()

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
        limit_amount=Decimal("500000.00"),
    )
    db.add(coverage)
    db.flush()

    resp = client.get(
        "/api/v1/products/prod-001/plans/plan-001",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == "plan-001"
    assert len(data["coverages"]) == 1
    assert data["coverages"][0]["name"] == "Hospitalization"
