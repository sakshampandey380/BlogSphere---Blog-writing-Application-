import pytest


def test_list_categories(client):
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1


def test_create_category_admin_only(client, admin_headers, user_headers):
    user_res = client.post(
        "/api/categories",
        json={"name": "DevOps", "description": "CI/CD & Kubernetes"},
        headers=user_headers,
    )
    assert user_res.status_code == 403

    admin_res = client.post(
        "/api/categories",
        json={"name": "DevOps", "description": "CI/CD & Kubernetes"},
        headers=admin_headers,
    )
    assert admin_res.status_code == 201
    assert admin_res.json()["data"]["name"] == "DevOps"


def test_list_tags(client):
    response = client.get("/api/tags")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_create_tag_authenticated(client, user_headers):
    response = client.post(
        "/api/tags",
        json={"name": "GraphQL"},
        headers=user_headers,
    )
    assert response.status_code in [200, 201]
    assert response.json()["data"]["name"] == "GraphQL"
