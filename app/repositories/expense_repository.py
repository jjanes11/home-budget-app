from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.expense import Expense
from app.schemas.expense import ExpenseFilters


class ExpenseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self, user_id: int):
        return self.db.query(Expense).filter(Expense.user_id == user_id)

    def get_by_id(self, user_id: int, expense_id: int) -> Expense | None:
        return self._base_query(user_id).filter(Expense.id == expense_id).first()

    def list_filtered(self, user_id: int, filters: ExpenseFilters) -> list[Expense]:
        q = self._base_query(user_id)

        if filters.category_id is not None:
            q = q.filter(Expense.category_id == filters.category_id)
        if filters.min_amount is not None:
            q = q.filter(Expense.amount >= filters.min_amount)
        if filters.max_amount is not None:
            q = q.filter(Expense.amount <= filters.max_amount)
        if filters.start_date is not None:
            q = q.filter(Expense.expense_date >= filters.start_date)
        if filters.end_date is not None:
            q = q.filter(Expense.expense_date <= filters.end_date)
        if filters.search:
            q = q.filter(Expense.description.ilike(f"%{filters.search}%"))

        sort_col = {
            "created_at": Expense.created_at,
            "amount": Expense.amount,
            "expense_date": Expense.expense_date,
        }[filters.sort_by]
        if filters.sort_order == "asc":
            q = q.order_by(sort_col.asc())
        else:
            q = q.order_by(sort_col.desc())

        return q.all()

    def create(
        self,
        user_id: int,
        category_id: int,
        description: str,
        amount: Decimal,
        expense_date: date,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            category_id=category_id,
            description=description,
            amount=amount,
            expense_date=expense_date,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense: Expense) -> None:
        self.db.delete(expense)
        self.db.commit()

    def summarize(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[Decimal, list[dict]]:
        q = self.db.query(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total"),
        ).join(Category, Expense.category_id == Category.id).filter(
            Expense.user_id == user_id
        )

        if start_date:
            q = q.filter(Expense.expense_date >= start_date)
        if end_date:
            q = q.filter(Expense.expense_date <= end_date)

        rows = q.group_by(Category.id, Category.name).all()

        total = sum((r.total for r in rows), Decimal(0))
        by_category = [
            {"category_id": r.category_id, "category_name": r.category_name, "total": r.total}
            for r in rows
        ]
        return total, by_category
