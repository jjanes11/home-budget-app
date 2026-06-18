"""Integration tests: authentication endpoints."""

from fastapi.testclient import TestClient


# ── startup / health ──────────────────────────────────────────────────────────

def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── register ──────────────────────────────────────────────────────────────────

def test_user_registration_success(client: TestClient):
    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data
    assert "id" in data


def test_register_duplicate_email_returns_409(client: TestClient, test_user):
    resp = client.post("/auth/register", json={"email": test_user.email, "password": "whatever"})
    assert resp.status_code == 409


def test_register_invalid_email_returns_422(client: TestClient):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "secret123"})
    assert resp.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────

def test_login_success_returns_jwt(client: TestClient, test_user):
    resp = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password_returns_401(client: TestClient, test_user):
    resp = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


def test_login_unknown_email_returns_401(client: TestClient):
    resp = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────

def test_me_returns_current_user(client: TestClient, test_user, headers):
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user.email


def test_protected_route_requires_auth(client: TestClient):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token_returns_401(client: TestClient):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
