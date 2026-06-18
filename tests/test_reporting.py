"""Integration tests: reporting endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from tests.conftest import make_category, make_expense, make_income


def _setup_data(db, user):
    """Create one category, one expense, and one income for the given user."""
    cat = make_category(db, user, "Work")
    exp = make_expense(db, user, cat, amount=Decimal("200.00"))
    inc = make_income(db, user, cat, amount=Decimal("1000.00"))
    return cat, exp, inc


# ── overview ─────────────────────────────────────────────────────────────────

def test_overview_totals_correct(client: TestClient, test_user, db, headers):
    _setup_data(db, test_user)

    resp = client.get("/reports/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_income"]) == 1000.0
    assert float(data["total_expenses"]) == 200.0
    assert data["period"] == "all_time"


def test_net_balance_calculation(client: TestClient, test_user, db, headers):
    _setup_data(db, test_user)

    resp = client.get("/reports/overview", headers=headers)
    data = resp.json()
    expected_net = float(data["total_income"]) - float(data["total_expenses"])
    assert float(data["net_balance"]) == expected_net


def test_overview_user_isolation(client: TestClient, test_user, test_user2, db, headers):
    """User2's data must not appear in user1's overview."""
    _setup_data(db, test_user2)

    resp = client.get("/reports/overview", headers=headers)
    data = resp.json()
    assert float(data["total_income"]) == 0.0
    assert float(data["total_expenses"]) == 0.0


def test_overview_period_month(client: TestClient, test_user, db, headers):
    """Period=month should filter by current month start."""
    _setup_data(db, test_user)  # income_date / expense_date = 2026-01-10/15 — may or may not be current month
    resp = client.get("/reports/overview?period=month", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "month"
    assert "total_income" in data


def test_overview_requires_auth(client: TestClient):
    resp = client.get("/reports/overview")
    assert resp.status_code == 401


# ── by-category ───────────────────────────────────────────────────────────────

def test_by_category_aggregation(client: TestClient, test_user, db, headers):
    _setup_data(db, test_user)

    resp = client.get("/reports/by-category", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "expenses_by_category" in data
    assert "income_by_category" in data

    # "Work" category must appear in both
    exp_names = [r["category_name"] for r in data["expenses_by_category"]]
    inc_names = [r["category_name"] for r in data["income_by_category"]]
    assert "Work" in exp_names
    assert "Work" in inc_names


def test_by_category_correct_totals(client: TestClient, test_user, db, headers):
    cat = make_category(db, test_user, "Groceries")
    make_expense(db, test_user, cat, amount=Decimal("50.00"))
    make_expense(db, test_user, cat, amount=Decimal("30.00"))

    resp = client.get("/reports/by-category", headers=headers)
    data = resp.json()
    groceries_row = next((r for r in data["expenses_by_category"] if r["category_name"] == "Groceries"), None)
    assert groceries_row is not None
    assert float(groceries_row["total"]) == 80.0


def test_income_vs_expense_separation(client: TestClient, test_user, db, headers):
    """Expenses must only appear in expenses_by_category, not income side."""
    cat = make_category(db, test_user, "Mixed")
    make_expense(db, test_user, cat, amount=Decimal("100.00"))
    # no income for this category

    resp = client.get("/reports/by-category", headers=headers)
    data = resp.json()
    inc_names = [r["category_name"] for r in data["income_by_category"]]
    assert "Mixed" not in inc_names


# ── monthly-trend ─────────────────────────────────────────────────────────────

def test_monthly_trend_generation(client: TestClient, test_user, db, headers):
    _setup_data(db, test_user)

    resp = client.get("/reports/monthly-trend", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) >= 1

    row = results[0]
    assert "month" in row
    assert "income" in row
    assert "expenses" in row
    assert "net" in row


def test_monthly_trend_net_is_income_minus_expenses(client: TestClient, test_user, db, headers):
    _setup_data(db, test_user)

    resp = client.get("/reports/monthly-trend", headers=headers)
    for row in resp.json():
        expected_net = float(row["income"]) - float(row["expenses"])
        assert abs(float(row["net"]) - expected_net) < 0.01
