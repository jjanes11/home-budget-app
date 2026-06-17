from datetime import date, timedelta
from decimal import Decimal
from typing import Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.income import Income
from app.repositories.category_repository import CategoryRepository
from app.repositories.income_repository import IncomeRepository
from app.schemas.income import IncomeCategorySummary, IncomeFilters, IncomeSummary


class IncomeService:
    def __init__(self, db: Session) -> None:
        self.repo = IncomeRepository(db)
        self.cat_repo = CategoryRepository(db)

    def _verify_category(self, user_id: int, category_id: Optional[int]) -> None:
        if category_id is None:
            return
        if not self.cat_repo.get_by_id(user_id, category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or does not belong to user",
            )

    def create_income(self, user_id: int, data) -> Income:
        self._verify_category(user_id, data.category_id)
        return self.repo.create(
            user_id=user_id,
            category_id=data.category_id,
            description=data.description,
            amount=data.amount,
            income_date=data.income_date,
        )

    def get_income_filtered(self, user_id: int, filters: IncomeFilters) -> list[Income]:
        return self.repo.list_filtered(user_id, filters)

    def get_income_by_id(self, user_id: int, income_id: int) -> Income:
        income = self.repo.get_by_id(user_id, income_id)
        if not income:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Income not found",
            )
        return income

    def delete_income(self, user_id: int, income_id: int) -> None:
        income = self.get_income_by_id(user_id, income_id)
        self.repo.delete(income)

    def get_income_summary(
        self,
        user_id: int,
        period: Literal["all_time", "week", "month", "year"] = "all_time",
    ) -> IncomeSummary:
        start_date: Optional[date] = None
        today = date.today()

        if period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today.replace(day=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)

        total, by_category = self.repo.summarize(user_id, start_date=start_date)
        return IncomeSummary(
            total_income=total,
            by_category=[IncomeCategorySummary(**row) for row in by_category],
            period=period,
        )
