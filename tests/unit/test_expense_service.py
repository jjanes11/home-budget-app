"""
Unit tests for ExpenseService.

All repository and DB dependencies are replaced with MagicMock instances.
No database or Docker is required.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.expense_service import ExpenseService

# Fixed "today" used to make date-range assertions deterministic.
FIXED_TODAY = date(2024, 6, 15)
USER_ID = 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def service() -> ExpenseService:
    """ExpenseService with both repositories replaced by MagicMocks."""
    svc = ExpenseService.__new__(ExpenseService)
    svc.repo = MagicMock()
    svc.cat_repo = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# _verify_category
# ---------------------------------------------------------------------------

class TestVerifyCategory:
    def test_raises_404_when_category_not_found(self, service):
        service.cat_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service._verify_category(USER_ID, category_id=99)
        assert exc_info.value.status_code == 404

    def test_returns_category_when_found(self, service):
        mock_cat = MagicMock()
        service.cat_repo.get_by_id.return_value = mock_cat
        result = service._verify_category(USER_ID, category_id=5)
        assert result is mock_cat


# ---------------------------------------------------------------------------
# create_expense
# ---------------------------------------------------------------------------

class TestCreateExpense:
    def test_delegates_to_repo_with_correct_args(self, service):
        service.cat_repo.get_by_id.return_value = MagicMock()
        mock_expense = MagicMock()
        service.repo.create.return_value = mock_expense

        data = MagicMock()
        data.category_id = 3
        data.description = "Groceries"
        data.amount = Decimal("42.50")
        data.expense_date = date(2024, 6, 10)

        result = service.create_expense(USER_ID, data)

        service.repo.create.assert_called_once_with(
            user_id=USER_ID,
            category_id=3,
            description="Groceries",
            amount=Decimal("42.50"),
            expense_date=date(2024, 6, 10),
        )
        assert result is mock_expense

    def test_raises_404_and_skips_create_when_category_missing(self, service):
        service.cat_repo.get_by_id.return_value = None
        data = MagicMock()
        data.category_id = 99

        with pytest.raises(HTTPException) as exc_info:
            service.create_expense(USER_ID, data)

        assert exc_info.value.status_code == 404
        service.repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# get_expense_by_id
# ---------------------------------------------------------------------------

class TestGetExpenseById:
    def test_raises_404_when_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.get_expense_by_id(USER_ID, expense_id=999)
        assert exc_info.value.status_code == 404

    def test_returns_expense_when_found(self, service):
        mock_expense = MagicMock()
        service.repo.get_by_id.return_value = mock_expense
        result = service.get_expense_by_id(USER_ID, expense_id=5)
        assert result is mock_expense


# ---------------------------------------------------------------------------
# delete_expense
# ---------------------------------------------------------------------------

class TestDeleteExpense:
    def test_calls_repo_delete_with_the_expense(self, service):
        mock_expense = MagicMock()
        service.repo.get_by_id.return_value = mock_expense

        service.delete_expense(USER_ID, expense_id=5)

        service.repo.delete.assert_called_once_with(mock_expense)

    def test_raises_404_when_expense_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.delete_expense(USER_ID, expense_id=999)
        assert exc_info.value.status_code == 404
        service.repo.delete.assert_not_called()


# ---------------------------------------------------------------------------
# get_summary — period → start_date resolution
# ---------------------------------------------------------------------------

class TestGetSummaryPeriod:
    """Verify that each period keyword maps to the correct start_date."""

    def _stub_repo(self, service, total=Decimal("0"), by_cat=None):
        service.repo.summarize.return_value = (total, by_cat or [])

    @patch("app.services.expense_service.date")
    def test_all_time_passes_none_start_date(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_summary(USER_ID, period="all_time")

        service.repo.summarize.assert_called_once_with(USER_ID, start_date=None)

    @patch("app.services.expense_service.date")
    def test_week_start_date_is_7_days_ago(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_summary(USER_ID, period="week")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 6, 8)
        )

    @patch("app.services.expense_service.date")
    def test_month_start_date_is_first_of_month(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_summary(USER_ID, period="month")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 6, 1)
        )

    @patch("app.services.expense_service.date")
    def test_year_start_date_is_jan_first(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_summary(USER_ID, period="year")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 1, 1)
        )

    def test_returns_expense_summary_with_correct_fields(self, service):
        service.repo.summarize.return_value = (
            Decimal("120.00"),
            [{"category_id": 1, "category_name": "Food", "total": Decimal("120.00")}],
        )

        result = service.get_summary(USER_ID, period="all_time")

        assert result.total_spent == Decimal("120.00")
        assert result.period == "all_time"
        assert len(result.by_category) == 1
        assert result.by_category[0].category_name == "Food"
        assert result.by_category[0].total == Decimal("120.00")

    def test_returns_empty_by_category_when_no_expenses(self, service):
        service.repo.summarize.return_value = (Decimal("0"), [])

        result = service.get_summary(USER_ID, period="all_time")

        assert result.total_spent == Decimal("0")
        assert result.by_category == []
