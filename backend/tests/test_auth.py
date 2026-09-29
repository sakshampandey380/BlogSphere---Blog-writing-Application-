import pytest


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "jane@example.com"
    assert data["data"]["user"]["name"] == "Jane Doe"


def test_register_duplicate_email(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Admin Clone",
            "email": "admin@test.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"].lower()


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Short Pwd",
            "email": "short@test.com",
            "password": "123",
        },
    )
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@test.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.com"


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@test.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "ghost@test.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_get_me_authenticated(client, user_headers):
    response = client.get("/api/auth/me", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "user1@test.com"


def test_get_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["success"] is False
