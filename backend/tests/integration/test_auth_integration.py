"""
Integration tests for the auth flow that exercise multiple layers together:
rate limiter, token denylist, and DB persistence.
"""
import pytest
from fastapi.testclient import TestClient


def test_refresh_token_rotation_prevents_reuse(client: TestClient, user, tenant):
    """A refresh token must be denied after it has been used once."""
    login = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password123"},
        headers={"X-Tenant-ID": tenant.id},
    )
    refresh_token = login.json()["data"]["refresh_token"]

    # First refresh — succeeds
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r1.status_code == 200

    # Second use of the same token — must be denied
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 401


def test_login_rate_limit(client: TestClient, user, tenant, monkeypatch):
    """Exceeding the per-IP login rate returns 429."""
    import app.api.v1.auth as auth_module

    call_count = 0

    def fake_check(key: str, max_requests: int, window_seconds: int = 60) -> bool:
        nonlocal call_count
        call_count += 1
        return call_count <= 1  # Only allow the first attempt

    monkeypatch.setattr(auth_module, "check_rate_limit", fake_check)

    # First attempt allowed
    r1 = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password123"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert r1.status_code == 200

    # Second attempt blocked
    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password123"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert r2.status_code == 429


def test_tenant_resolver_returns_name_and_id(client: TestClient, tenant):
    """Public /auth/tenant/<code> resolves correctly."""
    resp = client.get(f"/api/v1/auth/tenant/{tenant.code}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == tenant.id
    assert data["name"] == tenant.name


def test_tenant_resolver_404_for_unknown_code(client: TestClient):
    resp = client.get("/api/v1/auth/tenant/DOESNOTEXIST")
    assert resp.status_code == 404
