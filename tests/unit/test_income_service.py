"""
Unit tests for IncomeService.

All repository and DB dependencies are replaced with MagicMock instances.
No database or Docker is required.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.income_service import IncomeService

FIXED_TODAY = date(2024, 6, 15)
USER_ID = 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def service() -> IncomeService:
    """IncomeService with both repositories replaced by MagicMocks."""
    svc = IncomeService.__new__(IncomeService)
    svc.repo = MagicMock()
    svc.cat_repo = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# _verify_category
# ---------------------------------------------------------------------------

class TestVerifyCategory:
    def test_skips_repo_call_when_category_id_is_none(self, service):
        service._verify_category(USER_ID, category_id=None)
        service.cat_repo.get_by_id.assert_not_called()

    def test_raises_404_when_category_not_found(self, service):
        service.cat_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service._verify_category(USER_ID, category_id=42)
        assert exc_info.value.status_code == 404

    def test_does_not_raise_when_category_found(self, service):
        service.cat_repo.get_by_id.return_value = MagicMock()
        # Should not raise
        service._verify_category(USER_ID, category_id=5)


# ---------------------------------------------------------------------------
# create_income
# ---------------------------------------------------------------------------

class TestCreateIncome:
    def test_delegates_to_repo_with_correct_args(self, service):
        service.cat_repo.get_by_id.return_value = MagicMock()
        mock_income = MagicMock()
        service.repo.create.return_value = mock_income

        data = MagicMock()
        data.category_id = 2
        data.description = "Salary"
        data.amount = Decimal("3000.00")
        data.income_date = date(2024, 6, 1)

        result = service.create_income(USER_ID, data)

        service.repo.create.assert_called_once_with(
            user_id=USER_ID,
            category_id=2,
            description="Salary",
            amount=Decimal("3000.00"),
            income_date=date(2024, 6, 1),
        )
        assert result is mock_income

    def test_raises_404_and_skips_create_when_category_missing(self, service):
        service.cat_repo.get_by_id.return_value = None
        data = MagicMock()
        data.category_id = 99

        with pytest.raises(HTTPException) as exc_info:
            service.create_income(USER_ID, data)

        assert exc_info.value.status_code == 404
        service.repo.create.assert_not_called()

    def test_creates_income_with_no_category(self, service):
        """category_id=None is valid for income — no category check is performed."""
        mock_income = MagicMock()
        service.repo.create.return_value = mock_income

        data = MagicMock()
        data.category_id = None
        data.description = "Freelance"
        data.amount = Decimal("500.00")
        data.income_date = date(2024, 6, 5)

        result = service.create_income(USER_ID, data)

        service.cat_repo.get_by_id.assert_not_called()
        assert result is mock_income


# ---------------------------------------------------------------------------
# get_income_by_id
# ---------------------------------------------------------------------------

class TestGetIncomeById:
    def test_raises_404_when_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.get_income_by_id(USER_ID, income_id=999)
        assert exc_info.value.status_code == 404

    def test_returns_income_when_found(self, service):
        mock_income = MagicMock()
        service.repo.get_by_id.return_value = mock_income
        result = service.get_income_by_id(USER_ID, income_id=7)
        assert result is mock_income


# ---------------------------------------------------------------------------
# delete_income
# ---------------------------------------------------------------------------

class TestDeleteIncome:
    def test_calls_repo_delete_with_the_income(self, service):
        mock_income = MagicMock()
        service.repo.get_by_id.return_value = mock_income

        service.delete_income(USER_ID, income_id=7)

        service.repo.delete.assert_called_once_with(mock_income)

    def test_raises_404_when_income_not_found(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.delete_income(USER_ID, income_id=999)
        assert exc_info.value.status_code == 404
        service.repo.delete.assert_not_called()


# ---------------------------------------------------------------------------
# get_income_summary — period → start_date resolution
# ---------------------------------------------------------------------------

class TestGetIncomeSummaryPeriod:
    def _stub_repo(self, service, total=Decimal("0"), by_cat=None):
        service.repo.summarize.return_value = (total, by_cat or [])

    @patch("app.services.income_service.date")
    def test_all_time_passes_none_start_date(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_income_summary(USER_ID, period="all_time")

        service.repo.summarize.assert_called_once_with(USER_ID, start_date=None)

    @patch("app.services.income_service.date")
    def test_week_start_date_is_7_days_ago(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_income_summary(USER_ID, period="week")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 6, 8)
        )

    @patch("app.services.income_service.date")
    def test_month_start_date_is_first_of_month(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_income_summary(USER_ID, period="month")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 6, 1)
        )

    @patch("app.services.income_service.date")
    def test_year_start_date_is_jan_first(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        self._stub_repo(service)

        service.get_income_summary(USER_ID, period="year")

        service.repo.summarize.assert_called_once_with(
            USER_ID, start_date=date(2024, 1, 1)
        )

    def test_returns_income_summary_with_correct_fields(self, service):
        service.repo.summarize.return_value = (
            Decimal("3500.00"),
            [{"category_id": 2, "category_name": "Salary", "total": Decimal("3500.00")}],
        )

        result = service.get_income_summary(USER_ID, period="all_time")

        assert result.total_income == Decimal("3500.00")
        assert result.period == "all_time"
        assert len(result.by_category) == 1
        assert result.by_category[0].category_name == "Salary"
        assert result.by_category[0].total == Decimal("3500.00")

    def test_returns_empty_by_category_when_no_income(self, service):
        service.repo.summarize.return_value = (Decimal("0"), [])

        result = service.get_income_summary(USER_ID, period="all_time")

        assert result.total_income == Decimal("0")
        assert result.by_category == []
