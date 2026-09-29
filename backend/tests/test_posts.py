import pytest


def test_create_post_success(client, user_headers):
    payload = {
        "title": "Mastering FastAPI with Python 3.11",
        "excerpt": "A deep dive into high-performance async APIs.",
        "content": "<p>FastAPI is an incredible framework built on Starlette and Pydantic.</p>",
        "category_id": 1,
        "tags": ["Python", "FastAPI"],
        "status": "published",
        "is_featured": True,
    }
    response = client.post("/api/posts", json=payload, headers=user_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    post = data["data"]
    assert post["title"] == payload["title"]
    assert post["slug"] == "mastering-fastapi-with-python-311"
    assert post["reading_time_minutes"] >= 1
    assert post["author"]["id"] == 2
    assert len(post["tags"]) == 2


def test_html_sanitization_in_post(client, user_headers):
    payload = {
        "title": "Security Vulnerability Demonstration",
        "content": "<p>Safe text <script>alert('XSS Attack');</script><a href='javascript:evil()'>Malicious</a></p>",
        "category_id": 1,
        "status": "published",
    }
    response = client.post("/api/posts", json=payload, headers=user_headers)
    assert response.status_code == 201
    post = response.json()["data"]
    assert "<script>" not in post["content"]
    assert "alert('XSS Attack')" not in post["content"]
    assert "javascript:evil()" not in post["content"]


def test_create_post_unauthenticated(client):
    payload = {
        "title": "Unauthorized Post Attempt",
        "content": "<p>This should fail because no token was provided.</p>",
    }
    response = client.post("/api/posts", json=payload)
    assert response.status_code == 401


def test_get_posts_public(client, user_headers):
    client.post(
        "/api/posts",
        json={"title": "Public Article", "content": "<p>Content of public post</p>", "status": "published"},
        headers=user_headers,
    )
    client.post(
        "/api/posts",
        json={"title": "Secret Draft", "content": "<p>Content of secret draft</p>", "status": "draft"},
        headers=user_headers,
    )

    response = client.get("/api/posts")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert any(p["title"] == "Public Article" for p in items)
    assert not any(p["title"] == "Secret Draft" for p in items)


def test_author_can_view_own_draft(client, user_headers, user2_headers):
    create_res = client.post(
        "/api/posts",
        json={"title": "Author Draft Note", "content": "<p>Draft notes</p>", "status": "draft"},
        headers=user_headers,
    )
    slug = create_res.json()["data"]["slug"]

    res_author = client.get(f"/api/posts/slug/{slug}", headers=user_headers)
    assert res_author.status_code == 200

    res_other = client.get(f"/api/posts/slug/{slug}", headers=user2_headers)
    assert res_other.status_code in [403, 404]

    res_anon = client.get(f"/api/posts/slug/{slug}")
    assert res_anon.status_code == 404


def test_unauthorized_user_cannot_update_post(client, user_headers, user2_headers):
    create_res = client.post(
        "/api/posts",
        json={"title": "User One Original", "content": "<p>Original post</p>", "status": "published"},
        headers=user_headers,
    )
    post_id = create_res.json()["data"]["id"]

    put_res = client.put(
        f"/api/posts/{post_id}",
        json={"title": "Hacked Title"},
        headers=user2_headers,
    )
    assert put_res.status_code == 403
    assert "permission" in put_res.json()["message"].lower()


def test_admin_can_update_any_post(client, user_headers, admin_headers):
    create_res = client.post(
        "/api/posts",
        json={"title": "User Post for Admin Edit", "content": "<p>Original content</p>", "status": "published"},
        headers=user_headers,
    )
    post_id = create_res.json()["data"]["id"]

    admin_put = client.put(
        f"/api/posts/{post_id}",
        json={"title": "Admin Moderated Title"},
        headers=admin_headers,
    )
    assert admin_put.status_code == 200
    assert admin_put.json()["data"]["title"] == "Admin Moderated Title"


def test_search_and_category_filtering(client, user_headers):
    client.post(
        "/api/posts",
        json={"title": "Learning Rust for WebAssembly", "content": "<p>Rust programming guide</p>", "status": "published"},
        headers=user_headers,
    )
    client.post(
        "/api/posts",
        json={"title": "Advanced Python Metaprogramming", "content": "<p>Decorators and metaclasses</p>", "status": "published"},
        headers=user_headers,
    )

    search_res = client.get("/api/posts?search=Rust")
    assert search_res.status_code == 200
    items = search_res.json()["data"]["items"]
    assert len(items) == 1
    assert "Rust" in items[0]["title"]


def test_publish_and_unpublish(client, user_headers):
    create_res = client.post(
        "/api/posts",
        json={"title": "Toggle Post State", "content": "<p>Testing state change</p>", "status": "draft"},
        headers=user_headers,
    )
    post_id = create_res.json()["data"]["id"]

    pub_res = client.patch(f"/api/posts/{post_id}/publish", headers=user_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["status"] == "published"

    unpub_res = client.patch(f"/api/posts/{post_id}/unpublish", headers=user_headers)
    assert unpub_res.status_code == 200
    assert unpub_res.json()["data"]["status"] == "draft"


def test_delete_post(client, user_headers):
    create_res = client.post(
        "/api/posts",
        json={"title": "Post To Be Deleted", "content": "<p>Temporary content</p>", "status": "published"},
        headers=user_headers,
    )
    post_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/posts/{post_id}", headers=user_headers)
    assert del_res.status_code == 200

    get_res = client.get(f"/api/posts/{post_id}")
    assert get_res.status_code == 404
