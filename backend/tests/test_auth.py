import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, user, tenant):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@testco.com", "password": "password123"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_wrong_password(client: TestClient, user, tenant):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@testco.com", "password": "wrongpass"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert resp.status_code == 401


def test_login_no_tenant(client: TestClient, user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@testco.com", "password": "password123"},
    )
    assert resp.status_code == 400


def test_me_endpoint(client: TestClient, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "agent@testco.com"


def test_me_no_auth(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


def test_refresh_token(client: TestClient, user, tenant):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@testco.com", "password": "password123"},
        headers={"X-Tenant-ID": tenant.id},
    )
    refresh_token = login.json()["data"]["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
