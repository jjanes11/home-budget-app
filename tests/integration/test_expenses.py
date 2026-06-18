"""Integration tests: expenses endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from tests.integration.conftest import make_category, make_expense


# ── create ────────────────────────────────────────────────────────────────────

def test_create_expense_valid(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    resp = client.post(
        "/expenses",
        json={"category_id": cat.id, "description": "Groceries", "amount": 45.50, "expense_date": "2026-01-10"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Groceries"
    assert float(data["amount"]) == 45.50
    assert data["category"]["id"] == cat.id


def test_create_expense_invalid_amount(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    resp = client.post(
        "/expenses",
        json={"category_id": cat.id, "description": "Bad", "amount": -10, "expense_date": "2026-01-10"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_expense_invalid_category(client: TestClient, test_user, test_user2, db, headers):
    """Category belonging to user2 must be rejected for user1."""
    cat = make_category(db, test_user2, name="OtherCat")
    resp = client.post(
        "/expenses",
        json={"category_id": cat.id, "description": "Sneaky", "amount": 10.0, "expense_date": "2026-01-10"},
        headers=headers,
    )
    assert resp.status_code == 404


# ── list + filter ─────────────────────────────────────────────────────────────

def test_get_expenses_returns_own_only(client: TestClient, test_user, test_user2, db, headers):
    cat1 = make_category(db, test_user, "CatA")
    cat2 = make_category(db, test_user2, "CatB")
    make_expense(db, test_user, cat1, description="Mine")
    make_expense(db, test_user2, cat2, description="Theirs")

    resp = client.get("/expenses", headers=headers)
    assert resp.status_code == 200
    descriptions = [e["description"] for e in resp.json()]
    assert "Mine" in descriptions
    assert "Theirs" not in descriptions


def test_get_expenses_filter_by_category(client: TestClient, test_user, db, headers):
    cat1 = make_category(db, test_user, "Meals")
    cat2 = make_category(db, test_user, "Travel")
    make_expense(db, test_user, cat1, description="Lunch")
    make_expense(db, test_user, cat2, description="Bus")

    resp = client.get(f"/expenses?category_id={cat1.id}", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["description"] == "Lunch"


def test_get_expenses_filter_by_amount(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    make_expense(db, test_user, cat, amount=Decimal("20.00"), description="Small")
    make_expense(db, test_user, cat, amount=Decimal("200.00"), description="Large")

    resp = client.get("/expenses?min_amount=100", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["description"] == "Large"


def test_get_expenses_search(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    make_expense(db, test_user, cat, description="Coffee shop")
    make_expense(db, test_user, cat, description="Electricity bill")

    resp = client.get("/expenses?search=coffee", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert "Coffee" in results[0]["description"]


def test_sorting_expenses(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    make_expense(db, test_user, cat, amount=Decimal("10.00"))
    make_expense(db, test_user, cat, amount=Decimal("50.00"))

    resp = client.get("/expenses?sort_by=amount&sort_order=asc", headers=headers)
    amounts = [float(e["amount"]) for e in resp.json()]
    assert amounts == sorted(amounts)


# ── get by id ─────────────────────────────────────────────────────────────────

def test_get_expense_by_id(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    exp = make_expense(db, test_user, cat)
    resp = client.get(f"/expenses/{exp.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == exp.id


def test_expense_user_isolation(client: TestClient, test_user, test_user2, db, headers):
    cat = make_category(db, test_user2, "OtherCat")
    exp = make_expense(db, test_user2, cat)
    resp = client.get(f"/expenses/{exp.id}", headers=headers)
    assert resp.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_expense(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user)
    exp = make_expense(db, test_user, cat)
    resp = client.delete(f"/expenses/{exp.id}", headers=headers)
    assert resp.status_code == 204

    resp2 = client.get(f"/expenses/{exp.id}", headers=headers)
    assert resp2.status_code == 404


def test_delete_expense_not_found(client: TestClient, test_user, headers):
    resp = client.delete("/expenses/999999", headers=headers)
    assert resp.status_code == 404
