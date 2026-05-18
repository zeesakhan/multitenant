import pytest
import uuid
from fastapi.testclient import TestClient
from app.models.product import Product, Plan, Coverage
from app.constants.enums import ProductStatus, PlanType, CoverageType
from decimal import Decimal


@pytest.fixture
def active_product(db, tenant):
    product = Product(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name="Health Plus",
        code="HLTH001",
        status=ProductStatus.ACTIVE,
        description="Comprehensive health coverage",
    )
    db.add(product)
    db.flush()
    return product


@pytest.fixture
def active_plan(db, tenant, active_product):
    plan = Plan(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        product_id=active_product.id,
        name="Gold Plan",
        code="GOLD",
        plan_type=PlanType.FAMILY,
        base_premium=Decimal("1200.00"),
        description="Premium family coverage",
        is_active=True,
    )
    db.add(plan)
    db.flush()
    return plan


@pytest.fixture
def plan_with_coverage(db, tenant, active_plan):
    for name, ctype in [
        ("Hospitalization", CoverageType.HOSPITALIZATION),
        ("Dental", CoverageType.DENTAL),
    ]:
        cov = Coverage(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            plan_id=active_plan.id,
            name=name,
            coverage_type=ctype,
            limit_amount=Decimal("50000.00"),
            copay=Decimal("20.00"),
        )
        db.add(cov)
    db.flush()
    return active_plan


def _tenant_header(tenant):
    return {"X-Tenant-ID": tenant.id}


# ── GET /buy/products ─────────────────────────────────────────────────────────

def test_list_products_requires_tenant(client: TestClient):
    resp = client.get("/api/v1/buy/products")
    assert resp.status_code == 400


def test_list_products_empty(client: TestClient, tenant):
    resp = client.get("/api/v1/buy/products", headers=_tenant_header(tenant))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_list_products_only_active(client: TestClient, tenant, db, active_product):
    # Draft plan — should not appear
    Plan(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        product_id=active_product.id,
        name="Draft Plan",
        code="DRAFT",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("500.00"),
        is_active=False,
    )

    # Active plan
    p = Plan(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        product_id=active_product.id,
        name="Silver Plan",
        code="SILVER",
        plan_type=PlanType.INDIVIDUAL,
        base_premium=Decimal("800.00"),
        is_active=True,
    )
    db.add(p)
    db.flush()

    resp = client.get("/api/v1/buy/products", headers=_tenant_header(tenant))
    assert resp.status_code == 200
    products = resp.json()["data"]
    assert len(products) == 1
    assert len(products[0]["plans"]) == 1
    assert products[0]["plans"][0]["name"] == "Silver Plan"


def test_list_products_includes_coverages(client: TestClient, tenant, plan_with_coverage):
    resp = client.get("/api/v1/buy/products", headers=_tenant_header(tenant))
    assert resp.status_code == 200
    plans = resp.json()["data"][0]["plans"]
    assert len(plans) == 1
    assert len(plans[0]["coverages"]) == 2


# ── POST /buy/quote ───────────────────────────────────────────────────────────

def test_quote_calculates_premium(client: TestClient, tenant, active_plan):
    resp = client.post("/api/v1/buy/quote", json={
        "plan_id": active_plan.id,
        "members": [
            {"first_name": "Alice", "last_name": "Smith", "date_of_birth": "1985-03-15",
             "relationship": "self", "gender": "F"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_premium"] == 1200.00  # factor 1.0
    assert len(data["breakdown"]) == 1
    assert data["breakdown"][0]["relationship"] == "self"


def test_quote_family_premium(client: TestClient, tenant, active_plan):
    resp = client.post("/api/v1/buy/quote", json={
        "plan_id": active_plan.id,
        "members": [
            {"first_name": "Bob", "last_name": "Jones", "date_of_birth": "1980-01-01",
             "relationship": "self", "gender": "M"},
            {"first_name": "Carol", "last_name": "Jones", "date_of_birth": "1982-06-10",
             "relationship": "spouse", "gender": "F"},
            {"first_name": "Dan", "last_name": "Jones", "date_of_birth": "2010-09-20",
             "relationship": "child", "gender": "M"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 200
    data = resp.json()["data"]
    # 1200*1.0 + 1200*0.75 + 1200*0.35 = 1200 + 900 + 420 = 2520
    assert data["total_premium"] == 2520.0
    assert len(data["breakdown"]) == 3


def test_quote_requires_members(client: TestClient, tenant, active_plan):
    resp = client.post("/api/v1/buy/quote", json={
        "plan_id": active_plan.id, "members": [],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 400


def test_quote_invalid_plan(client: TestClient, tenant):
    resp = client.post("/api/v1/buy/quote", json={
        "plan_id": "nonexistent-plan", "members": [
            {"first_name": "X", "last_name": "Y", "date_of_birth": "1990-01-01",
             "relationship": "self", "gender": "M"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 404


# ── POST /buy/apply ───────────────────────────────────────────────────────────

_VALID_APPLY = {
    "email": "alice@example.com",
    "phone": "+1 555 123 4567",
    "members": [
        {"first_name": "Alice", "last_name": "Smith", "date_of_birth": "1985-03-15",
         "relationship": "self", "gender": "F"},
    ],
}


def test_apply_creates_application(client: TestClient, tenant, plan_with_coverage):
    resp = client.post("/api/v1/buy/apply", json={**_VALID_APPLY, "plan_id": plan_with_coverage.id},
                       headers=_tenant_header(tenant))
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["application_number"].startswith("APP-")
    assert data["status"] == "submitted"
    assert data["member_count"] == 1
    assert data["total_premium"] == 1200.0


def test_apply_family_creates_members(client: TestClient, tenant, plan_with_coverage, db):
    from app.models.application import Application
    from app.models.member import Member

    resp = client.post("/api/v1/buy/apply", json={
        "plan_id": plan_with_coverage.id,
        "email": "bob@example.com",
        "members": [
            {"first_name": "Bob", "last_name": "Jones", "date_of_birth": "1980-01-01",
             "relationship": "self", "gender": "M"},
            {"first_name": "Carol", "last_name": "Jones", "date_of_birth": "2010-05-12",
             "relationship": "child", "gender": "F"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 201
    app_id = resp.json()["data"]["application_id"]

    members = db.query(Member).filter(Member.application_id == app_id).all()
    assert len(members) == 2
    relationships = {m.relationship for m in members}
    assert "self" in relationships
    assert "child" in relationships


def test_apply_requires_self_member(client: TestClient, tenant, active_plan):
    resp = client.post("/api/v1/buy/apply", json={
        "plan_id": active_plan.id,
        "email": "x@example.com",
        "members": [
            {"first_name": "Bob", "last_name": "Jones", "date_of_birth": "2010-01-01",
             "relationship": "child", "gender": "M"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 400
    errors = resp.json().get("errors", [])
    assert any("self" in (e.get("message", "")).lower() for e in errors)


def test_apply_invalid_relationship(client: TestClient, tenant, active_plan):
    resp = client.post("/api/v1/buy/apply", json={
        "plan_id": active_plan.id,
        "email": "x@example.com",
        "members": [
            {"first_name": "Alice", "last_name": "Smith", "date_of_birth": "1985-01-01",
             "relationship": "self", "gender": "F"},
            {"first_name": "Bad", "last_name": "Member", "date_of_birth": "1990-01-01",
             "relationship": "enemy", "gender": "M"},
        ],
    }, headers=_tenant_header(tenant))
    assert resp.status_code == 422


def test_apply_creates_coverage_items(client: TestClient, tenant, plan_with_coverage, db):
    from app.models.application import ApplicationItem

    resp = client.post("/api/v1/buy/apply", json={**_VALID_APPLY, "plan_id": plan_with_coverage.id},
                       headers=_tenant_header(tenant))
    assert resp.status_code == 201
    app_id = resp.json()["data"]["application_id"]
    items = db.query(ApplicationItem).filter(ApplicationItem.application_id == app_id).all()
    assert len(items) == 2  # plan_with_coverage has 2 coverages


# ── GET /buy/apply/{id} ───────────────────────────────────────────────────────

def test_get_application_status(client: TestClient, tenant, plan_with_coverage):
    create_resp = client.post(
        "/api/v1/buy/apply",
        json={**_VALID_APPLY, "plan_id": plan_with_coverage.id},
        headers=_tenant_header(tenant),
    )
    app_id = create_resp.json()["data"]["application_id"]

    resp = client.get(f"/api/v1/buy/apply/{app_id}", headers=_tenant_header(tenant))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["application_id"] == app_id
    assert data["status"] == "submitted"
    assert data["customer_email"] == "alice@example.com"


def test_get_application_not_found(client: TestClient, tenant):
    resp = client.get("/api/v1/buy/apply/nonexistent", headers=_tenant_header(tenant))
    assert resp.status_code == 404
