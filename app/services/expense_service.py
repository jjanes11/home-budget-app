from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import CategorySummary, ExpenseFilters, ExpenseSummary


class ExpenseService:
    def __init__(self, db: Session) -> None:
        self.repo = ExpenseRepository(db)
        self.cat_repo = CategoryRepository(db)

    def _verify_category(self, user_id: int, category_id: int):
        cat = self.cat_repo.get_by_id(user_id, category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or does not belong to user",
            )
        return cat

    def create_expense(self, user_id: int, data) -> Expense:
        self._verify_category(user_id, data.category_id)
        return self.repo.create(
            user_id=user_id,
            category_id=data.category_id,
            description=data.description,
            amount=data.amount,
            expense_date=data.expense_date,
        )

    def get_expenses_filtered(self, user_id: int, filters: ExpenseFilters) -> list[Expense]:
        return self.repo.list_filtered(user_id, filters)

    def get_expense_by_id(self, user_id: int, expense_id: int) -> Expense:
        expense = self.repo.get_by_id(user_id, expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )
        return expense

    def delete_expense(self, user_id: int, expense_id: int) -> None:
        expense = self.get_expense_by_id(user_id, expense_id)
        self.repo.delete(expense)

    def get_summary(
        self,
        user_id: int,
        period: Literal["all_time", "week", "month", "year"] = "all_time",
    ) -> ExpenseSummary:
        start_date: Optional[date] = None
        today = date.today()

        if period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today.replace(day=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)

        total, by_category = self.repo.summarize(user_id, start_date=start_date)
        return ExpenseSummary(
            total_spent=total,
            by_category=[CategorySummary(**row) for row in by_category],
            period=period,
        )
