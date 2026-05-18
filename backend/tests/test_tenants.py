import uuid
import pytest


def make_code() -> str:
    return f"TN{uuid.uuid4().hex[:6].upper()}"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def payload():
    return {
        "code": make_code(),
        "name": "Acme Insurance",
        "contact_email": "admin@acme.com",
        "contact_phone": "+1 555 000 0001",
        "country": "US",
        "currency": "USD",
        "timezone": "UTC",
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_list_tenants_requires_auth(client):
    res = client.get("/api/v1/tenants")
    assert res.status_code in (401, 403)


def test_list_tenants_as_super_admin(client, super_admin_headers):
    res = client.get("/api/v1/tenants", headers=super_admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert "data" in body


def test_create_tenant(client, super_admin_headers, payload):
    res = client.post("/api/v1/tenants", json=payload, headers=super_admin_headers)
    assert res.status_code in (200, 201)
    data = res.json()["data"]
    assert data["code"] == payload["code"]
    assert data["name"] == payload["name"]


def test_create_tenant_duplicate_code_returns_409(client, super_admin_headers, payload):
    client.post("/api/v1/tenants", json=payload, headers=super_admin_headers)
    res = client.post("/api/v1/tenants", json=payload, headers=super_admin_headers)
    assert res.status_code == 409


def test_get_tenant(client, super_admin_headers, payload):
    create_res = client.post("/api/v1/tenants", json=payload, headers=super_admin_headers)
    assert create_res.status_code in (200, 201)
    tenant_id = create_res.json()["data"]["id"]

    res = client.get(f"/api/v1/tenants/{tenant_id}", headers=super_admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == tenant_id


def test_get_tenant_not_found(client, super_admin_headers):
    res = client.get(f"/api/v1/tenants/{uuid.uuid4()}", headers=super_admin_headers)
    assert res.status_code == 404


def test_update_tenant(client, super_admin_headers, payload):
    create_res = client.post("/api/v1/tenants", json=payload, headers=super_admin_headers)
    tenant_id = create_res.json()["data"]["id"]

    res = client.put(
        f"/api/v1/tenants/{tenant_id}",
        json={"name": "Acme Insurance Updated", "status": "active"},
        headers=super_admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Acme Insurance Updated"


def test_tenant_admin_cannot_create_tenant(client, admin_headers, payload):
    res = client.post("/api/v1/tenants", json=payload, headers=admin_headers)
    assert res.status_code == 403
