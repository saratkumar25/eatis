"""
tests/test_auth.py
────────────────────
Tests for registration, login, and JWT-protected routes.
"""


def test_register_and_login(client):
    # Register
    resp = client.post("/api/v1/auth/register", json={
        "name": "Test Officer",
        "email": "officer@eatis.gov",
        "password": "SecurePass123",
        "role": "operator",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "officer@eatis.gov"
    assert "hashed_password" not in body

    # Duplicate registration should fail
    resp2 = client.post("/api/v1/auth/register", json={
        "name": "Test Officer",
        "email": "officer@eatis.gov",
        "password": "SecurePass123",
    })
    assert resp2.status_code == 409

    # Login
    resp3 = client.post("/api/v1/auth/login", json={
        "email": "officer@eatis.gov",
        "password": "SecurePass123",
    })
    assert resp3.status_code == 200
    token_data = resp3.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # /me with token
    token = token_data["access_token"]
    resp4 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 200
    assert resp4.json()["email"] == "officer@eatis.gov"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "name": "User",
        "email": "user@eatis.gov",
        "password": "CorrectPass123",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "user@eatis.gov",
        "password": "WrongPass123",
    })
    assert resp.status_code == 401


def test_protected_route_without_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


def test_weak_password_rejected(client):
    resp = client.post("/api/v1/auth/register", json={
        "name": "User",
        "email": "weak@eatis.gov",
        "password": "short",
    })
    assert resp.status_code == 422
