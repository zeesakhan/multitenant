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


def test_forgot_password_always_200(client: TestClient, tenant):
    """Endpoint must always return 200 regardless of whether the email exists (prevents enumeration)."""
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@nowhere.com"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert resp.status_code == 200


def test_forgot_password_sends_token_for_existing_user(client: TestClient, user, tenant):
    """Token is created when a real user's email is submitted."""
    from app.utils.reset_tokens import _tokens

    before = len(_tokens)
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": user.email},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert len(_tokens) > before


def test_reset_password_with_valid_token(client: TestClient, user, tenant):
    """Valid token allows password to be reset and is then consumed."""
    from app.utils.reset_tokens import create as create_reset_token, _tokens

    token = create_reset_token(user.id)
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newpassword99"},
    )
    assert resp.status_code == 200
    # Token must be consumed — cannot be reused
    assert token not in _tokens


def test_reset_password_invalid_token(client: TestClient):
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bogus-token", "new_password": "doesntmatter"},
    )
    assert resp.status_code == 400


def test_reset_password_min_length(client: TestClient, user):
    """Passwords shorter than 8 chars must be rejected before token consumption."""
    from app.utils.reset_tokens import create as create_reset_token

    token = create_reset_token(user.id)
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "short"},
    )
    assert resp.status_code == 422


def test_reset_password_allows_login_with_new_password(client: TestClient, user, tenant):
    """After reset, the user can log in with the new password."""
    from app.utils.reset_tokens import create as create_reset_token

    token = create_reset_token(user.id)
    client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "freshpass99"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "freshpass99"},
        headers={"X-Tenant-ID": tenant.id},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]
