from datetime import date, timedelta
from decimal import Decimal
from typing import Literal, Optional

from sqlalchemy.orm import Session

from app.repositories.expense_repository import ExpenseRepository
from app.repositories.income_repository import IncomeRepository


def _date_range(
    period: str,
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[Optional[date], Optional[date]]:
    """Resolve effective start/end dates from period or explicit params."""
    if start_date or end_date:
        return start_date, end_date

    today = date.today()
    if period == "month":
        return today.replace(day=1), today
    if period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=quarter_start_month, day=1), today
    if period == "year":
        return today.replace(month=1, day=1), today
    return None, None  # all_time


class ReportService:
    def __init__(self, db: Session) -> None:
        self.expense_repo = ExpenseRepository(db)
        self.income_repo = IncomeRepository(db)

    def get_overview(
        self,
        user_id: int,
        period: str = "all_time",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        sd, ed = _date_range(period, start_date, end_date)
        total_income = self.income_repo.sum_by_user(user_id, sd, ed)
        total_expenses = self.expense_repo.sum_by_user(user_id, sd, ed)
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": total_income - total_expenses,
            "period": period,
        }

    def get_by_category(self, user_id: int) -> dict:
        _, expenses_by_category = self.expense_repo.summarize(user_id)
        _, income_by_category = self.income_repo.summarize(user_id)
        return {
            "expenses_by_category": expenses_by_category,
            "income_by_category": income_by_category,
        }

    def get_monthly_trend(self, user_id: int) -> list[dict]:
        expense_rows = {r["month"]: r["total"] for r in self.expense_repo.group_by_month(user_id)}
        income_rows = {r["month"]: r["total"] for r in self.income_repo.group_by_month(user_id)}

        all_months = sorted(set(expense_rows) | set(income_rows))
        return [
            {
                "month": month,
                "income": income_rows.get(month, Decimal(0)),
                "expenses": expense_rows.get(month, Decimal(0)),
                "net": income_rows.get(month, Decimal(0)) - expense_rows.get(month, Decimal(0)),
            }
            for month in all_months
        ]
