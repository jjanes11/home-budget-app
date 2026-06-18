"""Integration tests: income endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from tests.integration.conftest import make_category, make_income


# ── create ────────────────────────────────────────────────────────────────────

def test_create_income(client: TestClient, test_user, db, headers):
    resp = client.post(
        "/incomes",
        json={"description": "Salary", "amount": 3000.0, "income_date": "2026-01-01"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Salary"
    assert float(data["amount"]) == 3000.0
    assert data["category"] is None


def test_create_income_with_category(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user, "Work")
    resp = client.post(
        "/incomes",
        json={"category_id": cat.id, "description": "Freelance", "amount": 500.0, "income_date": "2026-01-05"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["category"]["name"] == "Work"


def test_create_income_invalid_amount(client: TestClient, test_user, headers):
    resp = client.post(
        "/incomes",
        json={"description": "Bad", "amount": 0, "income_date": "2026-01-01"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_income_invalid_category(client: TestClient, test_user, test_user2, db, headers):
    cat = make_category(db, test_user2, "OtherCat")
    resp = client.post(
        "/incomes",
        json={"category_id": cat.id, "description": "Sneaky", "amount": 100.0, "income_date": "2026-01-01"},
        headers=headers,
    )
    assert resp.status_code == 404


# ── list ─────────────────────────────────────────────────────────────────────

def test_get_income_list(client: TestClient, test_user, db, headers):
    make_income(db, test_user, description="Salary")
    make_income(db, test_user, description="Bonus")

    resp = client.get("/incomes", headers=headers)
    assert resp.status_code == 200
    descriptions = [i["description"] for i in resp.json()]
    assert "Salary" in descriptions
    assert "Bonus" in descriptions


def test_income_user_isolation(client: TestClient, test_user, test_user2, db, headers):
    make_income(db, test_user, description="Mine")
    make_income(db, test_user2, description="Theirs")

    resp = client.get("/incomes", headers=headers)
    descriptions = [i["description"] for i in resp.json()]
    assert "Mine" in descriptions
    assert "Theirs" not in descriptions


# ── filtering ────────────────────────────────────────────────────────────────

def test_income_filter_by_min_amount(client: TestClient, test_user, db, headers):
    make_income(db, test_user, amount=Decimal("100.00"), description="Small")
    make_income(db, test_user, amount=Decimal("5000.00"), description="Large")

    resp = client.get("/incomes?min_amount=1000", headers=headers)
    results = resp.json()
    assert len(results) == 1
    assert results[0]["description"] == "Large"


def test_income_filter_search(client: TestClient, test_user, db, headers):
    make_income(db, test_user, description="Monthly salary")
    make_income(db, test_user, description="Side project payment")

    resp = client.get("/incomes?search=salary", headers=headers)
    results = resp.json()
    assert len(results) == 1
    assert "salary" in results[0]["description"].lower()


def test_income_sort_by_amount_asc(client: TestClient, test_user, db, headers):
    make_income(db, test_user, amount=Decimal("300.00"))
    make_income(db, test_user, amount=Decimal("100.00"))
    make_income(db, test_user, amount=Decimal("200.00"))

    resp = client.get("/incomes?sort_by=amount&sort_order=asc", headers=headers)
    amounts = [float(i["amount"]) for i in resp.json()]
    assert amounts == sorted(amounts)


# ── get by id ─────────────────────────────────────────────────────────────────

def test_get_income_by_id(client: TestClient, test_user, db, headers):
    inc = make_income(db, test_user)
    resp = client.get(f"/incomes/{inc.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == inc.id


def test_get_income_other_user_returns_404(client: TestClient, test_user, test_user2, db, headers):
    inc = make_income(db, test_user2)
    resp = client.get(f"/incomes/{inc.id}", headers=headers)
    assert resp.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_income(client: TestClient, test_user, db, headers):
    inc = make_income(db, test_user)
    resp = client.delete(f"/incomes/{inc.id}", headers=headers)
    assert resp.status_code == 204

    resp2 = client.get(f"/incomes/{inc.id}", headers=headers)
    assert resp2.status_code == 404


def test_delete_income_not_found(client: TestClient, test_user, headers):
    resp = client.delete("/incomes/999999", headers=headers)
    assert resp.status_code == 404
