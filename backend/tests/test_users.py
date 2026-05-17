import pytest
import uuid
from fastapi.testclient import TestClient
from app.models.user import User
from app.constants.enums import UserType, UserStatus
from app.services.user_service import hash_password


def _new_user(db, tenant_id: str) -> User:
    u = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=f"extra_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass123"),
        first_name="Extra",
        last_name="User",
        user_type=UserType.AGENT,
        status=UserStatus.ACTIVE,
    )
    db.add(u)
    db.flush()
    return u


def test_list_users(client: TestClient, admin_headers):
    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_list_users_requires_auth(client: TestClient):
    resp = client.get("/api/v1/users")
    assert resp.status_code in (401, 403)


def test_create_user(client: TestClient, admin_headers):
    payload = {
        "email": f"new_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Secure123!",
        "first_name": "New",
        "last_name": "Member",
        "user_type": "agent",
        "role_ids": [],
    }
    resp = client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == payload["email"]


def test_create_duplicate_user_returns_409(client: TestClient, admin_headers, user):
    payload = {
        "email": "agent@testco.com",
        "password": "pass123",
        "first_name": "Dup",
        "last_name": "User",
        "user_type": "agent",
        "role_ids": [],
    }
    resp = client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert resp.status_code == 409


def test_get_user(client: TestClient, admin_headers, user):
    resp = client.get(f"/api/v1/users/{user.id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == user.id
    assert data["email"] == user.email


def test_get_user_from_other_tenant_returns_404(client: TestClient, admin_headers, super_admin):
    resp = client.get(f"/api/v1/users/{super_admin.id}", headers=admin_headers)
    assert resp.status_code == 404


def test_update_user(client: TestClient, admin_headers, user):
    resp = client.put(
        f"/api/v1/users/{user.id}",
        json={"first_name": "Updated"},
        headers=admin_headers,
    )
    assert resp.status_code == 200


def test_deactivate_user(client: TestClient, admin_headers, tenant, db):
    u = _new_user(db, tenant.id)
    resp = client.delete(f"/api/v1/users/{u.id}", headers=admin_headers)
    assert resp.status_code == 200


def test_list_roles(client: TestClient, admin_headers):
    resp = client.get("/api/v1/roles", headers=admin_headers)
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_create_role(client: TestClient, admin_headers):
    resp = client.post(
        "/api/v1/roles",
        json={"name": f"reviewer_{uuid.uuid4().hex[:4]}", "description": "Claims reviewer", "permission_ids": []},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert "id" in resp.json()["data"]
