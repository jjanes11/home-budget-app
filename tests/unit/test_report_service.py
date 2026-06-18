"""
Unit tests for report_service.

Covers:
  - _date_range() pure function — all periods and explicit date overrides
  - ReportService.get_overview() — net balance calculation and period delegation
  - ReportService.get_monthly_trend() — month merging, net computation,
    missing-month zero defaults
  - ReportService.get_by_category() — delegation to repos

No database or Docker is required.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_service import ReportService, _date_range

FIXED_TODAY = date(2024, 6, 15)  # Q2, mid-month
USER_ID = 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def service() -> ReportService:
    """ReportService with both repositories replaced by MagicMocks."""
    svc = ReportService.__new__(ReportService)
    svc.expense_repo = MagicMock()
    svc.income_repo = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# _date_range — pure function
# ---------------------------------------------------------------------------

class TestDateRange:
    """Tests for the module-level _date_range helper."""

    @patch("app.services.report_service.date")
    def test_all_time_returns_none_none(self, mock_date):
        mock_date.today.return_value = FIXED_TODAY
        sd, ed = _date_range("all_time", None, None)
        assert sd is None
        assert ed is None

    @patch("app.services.report_service.date")
    def test_month_starts_on_first_of_current_month(self, mock_date):
        mock_date.today.return_value = FIXED_TODAY
        sd, ed = _date_range("month", None, None)
        assert sd == date(2024, 6, 1)
        assert ed == FIXED_TODAY

    @patch("app.services.report_service.date")
    def test_quarter_q2_starts_april_first(self, mock_date):
        # June → Q2 → quarter_start_month = ((6-1)//3)*3+1 = 4
        mock_date.today.return_value = FIXED_TODAY
        sd, ed = _date_range("quarter", None, None)
        assert sd == date(2024, 4, 1)
        assert ed == FIXED_TODAY

    @patch("app.services.report_service.date")
    def test_quarter_q1_starts_january_first(self, mock_date):
        mock_date.today.return_value = date(2024, 2, 20)
        sd, ed = _date_range("quarter", None, None)
        assert sd == date(2024, 1, 1)

    @patch("app.services.report_service.date")
    def test_quarter_q3_starts_july_first(self, mock_date):
        mock_date.today.return_value = date(2024, 8, 5)
        sd, ed = _date_range("quarter", None, None)
        assert sd == date(2024, 7, 1)

    @patch("app.services.report_service.date")
    def test_quarter_q4_starts_october_first(self, mock_date):
        mock_date.today.return_value = date(2024, 11, 1)
        sd, ed = _date_range("quarter", None, None)
        assert sd == date(2024, 10, 1)

    @patch("app.services.report_service.date")
    def test_year_starts_jan_first_of_current_year(self, mock_date):
        mock_date.today.return_value = FIXED_TODAY
        sd, ed = _date_range("year", None, None)
        assert sd == date(2024, 1, 1)
        assert ed == FIXED_TODAY

    def test_explicit_start_date_overrides_period(self):
        explicit_start = date(2023, 1, 1)
        sd, ed = _date_range("month", explicit_start, None)
        assert sd == explicit_start
        assert ed is None

    def test_explicit_end_date_overrides_period(self):
        explicit_end = date(2024, 3, 31)
        sd, ed = _date_range("year", None, explicit_end)
        assert sd is None
        assert ed == explicit_end

    def test_both_explicit_dates_override_period(self):
        explicit_start = date(2024, 1, 1)
        explicit_end = date(2024, 3, 31)
        sd, ed = _date_range("quarter", explicit_start, explicit_end)
        assert sd == explicit_start
        assert ed == explicit_end


# ---------------------------------------------------------------------------
# ReportService.get_overview
# ---------------------------------------------------------------------------

class TestGetOverview:
    def test_net_balance_is_income_minus_expenses(self, service):
        service.income_repo.sum_by_user.return_value = Decimal("5000.00")
        service.expense_repo.sum_by_user.return_value = Decimal("3200.00")

        result = service.get_overview(USER_ID, period="all_time")

        assert result["total_income"] == Decimal("5000.00")
        assert result["total_expenses"] == Decimal("3200.00")
        assert result["net_balance"] == Decimal("1800.00")

    def test_net_balance_is_negative_when_overspent(self, service):
        service.income_repo.sum_by_user.return_value = Decimal("1000.00")
        service.expense_repo.sum_by_user.return_value = Decimal("1500.00")

        result = service.get_overview(USER_ID, period="all_time")

        assert result["net_balance"] == Decimal("-500.00")

    def test_period_is_included_in_result(self, service):
        service.income_repo.sum_by_user.return_value = Decimal("0")
        service.expense_repo.sum_by_user.return_value = Decimal("0")

        result = service.get_overview(USER_ID, period="month")

        assert result["period"] == "month"

    @patch("app.services.report_service.date")
    def test_month_period_passes_resolved_dates_to_repos(self, mock_date, service):
        mock_date.today.return_value = FIXED_TODAY
        service.income_repo.sum_by_user.return_value = Decimal("0")
        service.expense_repo.sum_by_user.return_value = Decimal("0")

        service.get_overview(USER_ID, period="month")

        service.income_repo.sum_by_user.assert_called_once_with(
            USER_ID, date(2024, 6, 1), FIXED_TODAY
        )
        service.expense_repo.sum_by_user.assert_called_once_with(
            USER_ID, date(2024, 6, 1), FIXED_TODAY
        )

    def test_explicit_dates_override_period_for_repos(self, service):
        service.income_repo.sum_by_user.return_value = Decimal("0")
        service.expense_repo.sum_by_user.return_value = Decimal("0")
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)

        service.get_overview(USER_ID, period="all_time", start_date=start, end_date=end)

        service.income_repo.sum_by_user.assert_called_once_with(USER_ID, start, end)
        service.expense_repo.sum_by_user.assert_called_once_with(USER_ID, start, end)


# ---------------------------------------------------------------------------
# ReportService.get_monthly_trend
# ---------------------------------------------------------------------------

class TestGetMonthlyTrend:
    def test_merges_expense_and_income_months(self, service):
        service.expense_repo.group_by_month.return_value = [
            {"month": "2024-04", "total": Decimal("400.00")},
        ]
        service.income_repo.group_by_month.return_value = [
            {"month": "2024-05", "total": Decimal("3000.00")},
        ]

        result = service.get_monthly_trend(USER_ID)

        months = [row["month"] for row in result]
        assert months == ["2024-04", "2024-05"]

    def test_months_are_sorted_chronologically(self, service):
        service.expense_repo.group_by_month.return_value = [
            {"month": "2024-06", "total": Decimal("100.00")},
            {"month": "2024-03", "total": Decimal("50.00")},
        ]
        service.income_repo.group_by_month.return_value = [
            {"month": "2024-01", "total": Decimal("2000.00")},
        ]

        result = service.get_monthly_trend(USER_ID)

        months = [row["month"] for row in result]
        assert months == ["2024-01", "2024-03", "2024-06"]

    def test_net_is_income_minus_expenses_per_month(self, service):
        service.expense_repo.group_by_month.return_value = [
            {"month": "2024-05", "total": Decimal("800.00")},
        ]
        service.income_repo.group_by_month.return_value = [
            {"month": "2024-05", "total": Decimal("3000.00")},
        ]

        result = service.get_monthly_trend(USER_ID)

        assert len(result) == 1
        assert result[0]["net"] == Decimal("2200.00")

    def test_missing_expense_month_defaults_to_zero(self, service):
        """A month with income but no expenses should have expenses=0."""
        service.expense_repo.group_by_month.return_value = []
        service.income_repo.group_by_month.return_value = [
            {"month": "2024-05", "total": Decimal("1500.00")},
        ]

        result = service.get_monthly_trend(USER_ID)

        assert result[0]["expenses"] == Decimal(0)
        assert result[0]["income"] == Decimal("1500.00")
        assert result[0]["net"] == Decimal("1500.00")

    def test_missing_income_month_defaults_to_zero(self, service):
        """A month with expenses but no income should have income=0."""
        service.expense_repo.group_by_month.return_value = [
            {"month": "2024-05", "total": Decimal("600.00")},
        ]
        service.income_repo.group_by_month.return_value = []

        result = service.get_monthly_trend(USER_ID)

        assert result[0]["income"] == Decimal(0)
        assert result[0]["expenses"] == Decimal("600.00")
        assert result[0]["net"] == Decimal("-600.00")

    def test_returns_empty_list_when_no_data(self, service):
        service.expense_repo.group_by_month.return_value = []
        service.income_repo.group_by_month.return_value = []

        result = service.get_monthly_trend(USER_ID)

        assert result == []

    def test_multiple_months_all_have_correct_net(self, service):
        service.expense_repo.group_by_month.return_value = [
            {"month": "2024-01", "total": Decimal("500.00")},
            {"month": "2024-02", "total": Decimal("300.00")},
        ]
        service.income_repo.group_by_month.return_value = [
            {"month": "2024-01", "total": Decimal("2000.00")},
            {"month": "2024-02", "total": Decimal("2000.00")},
        ]

        result = service.get_monthly_trend(USER_ID)

        assert result[0]["net"] == Decimal("1500.00")
        assert result[1]["net"] == Decimal("1700.00")


# ---------------------------------------------------------------------------
# ReportService.get_by_category
# ---------------------------------------------------------------------------

class TestGetByCategory:
    def test_returns_expense_and_income_category_data(self, service):
        expense_rows = [{"category_id": 1, "category_name": "Food", "total": Decimal("200")}]
        income_rows = [{"category_id": 2, "category_name": "Salary", "total": Decimal("3000")}]
        service.expense_repo.summarize.return_value = (Decimal("200"), expense_rows)
        service.income_repo.summarize.return_value = (Decimal("3000"), income_rows)

        result = service.get_by_category(USER_ID)

        assert result["expenses_by_category"] == expense_rows
        assert result["income_by_category"] == income_rows

    def test_calls_repos_with_correct_user_id(self, service):
        service.expense_repo.summarize.return_value = (Decimal("0"), [])
        service.income_repo.summarize.return_value = (Decimal("0"), [])

        service.get_by_category(USER_ID)

        service.expense_repo.summarize.assert_called_once_with(USER_ID)
        service.income_repo.summarize.assert_called_once_with(USER_ID)
