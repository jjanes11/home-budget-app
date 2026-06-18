"""Integration tests: categories endpoints."""

from fastapi.testclient import TestClient

from tests.integration.conftest import make_category


# ── create ────────────────────────────────────────────────────────────────────

def test_create_category(client: TestClient, test_user, headers):
    resp = client.post("/categories", json={"name": "Hobbies"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Hobbies"
    assert "id" in data


def test_create_category_name_is_normalized(client: TestClient, test_user, headers):
    resp = client.post("/categories", json={"name": "  food expenses  "}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Food Expenses"


def test_duplicate_category_returns_409(client: TestClient, test_user, db, headers):
    make_category(db, test_user, name="Savings")
    resp = client.post("/categories", json={"name": "Savings"}, headers=headers)
    assert resp.status_code == 409


# ── list ─────────────────────────────────────────────────────────────────────

def test_list_categories_only_returns_own(client: TestClient, test_user, test_user2, db, headers, headers2):
    make_category(db, test_user, name="UserOneCat")
    make_category(db, test_user2, name="UserTwoCat")

    resp = client.get("/categories", headers=headers)
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "UserOneCat" in names
    assert "UserTwoCat" not in names


def test_list_categories_requires_auth(client: TestClient):
    resp = client.get("/categories")
    assert resp.status_code == 401


# ── get by id ─────────────────────────────────────────────────────────────────

def test_get_category_by_id(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user, name="Sports")
    resp = client.get(f"/categories/{cat.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Sports"


def test_category_ownership_isolation(client: TestClient, test_user, test_user2, db, headers):
    """User 2's category must not be accessible by user 1."""
    cat = make_category(db, test_user2, name="Private")
    resp = client.get(f"/categories/{cat.id}", headers=headers)
    assert resp.status_code == 404


# ── update ────────────────────────────────────────────────────────────────────

def test_update_category(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user, name="Old Name")
    resp = client.put(f"/categories/{cat.id}", json={"name": "new name"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_update_category_duplicate_name_returns_409(client: TestClient, test_user, db, headers):
    make_category(db, test_user, name="Alpha")
    cat2 = make_category(db, test_user, name="Beta")
    resp = client.put(f"/categories/{cat2.id}", json={"name": "Alpha"}, headers=headers)
    assert resp.status_code == 409


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_category(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user, name="Temporary")
    resp = client.delete(f"/categories/{cat.id}", headers=headers)
    assert resp.status_code == 204


def test_delete_category_not_found(client: TestClient, test_user, headers):
    resp = client.delete("/categories/999999", headers=headers)
    assert resp.status_code == 404
