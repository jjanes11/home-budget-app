from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.income import Income
from app.schemas.income import IncomeFilters


class IncomeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self, user_id: int):
        return self.db.query(Income).filter(Income.user_id == user_id)

    def get_by_id(self, user_id: int, income_id: int) -> Income | None:
        return self._base_query(user_id).filter(Income.id == income_id).first()

    def list_filtered(self, user_id: int, filters: IncomeFilters) -> list[Income]:
        q = self._base_query(user_id)

        if filters.category_id is not None:
            q = q.filter(Income.category_id == filters.category_id)
        if filters.min_amount is not None:
            q = q.filter(Income.amount >= filters.min_amount)
        if filters.max_amount is not None:
            q = q.filter(Income.amount <= filters.max_amount)
        if filters.start_date is not None:
            q = q.filter(Income.income_date >= filters.start_date)
        if filters.end_date is not None:
            q = q.filter(Income.income_date <= filters.end_date)
        if filters.search:
            q = q.filter(Income.description.ilike(f"%{filters.search}%"))

        sort_col = {
            "created_at": Income.created_at,
            "amount": Income.amount,
            "income_date": Income.income_date,
        }.get(filters.sort_by, Income.created_at)
        if filters.sort_order == "asc":
            q = q.order_by(sort_col.asc())
        else:
            q = q.order_by(sort_col.desc())

        return q.all()

    def create(
        self,
        user_id: int,
        category_id: Optional[int],
        description: str,
        amount: Decimal,
        income_date: date,
    ) -> Income:
        income = Income(
            user_id=user_id,
            category_id=category_id,
            description=description,
            amount=amount,
            income_date=income_date,
        )
        self.db.add(income)
        self.db.commit()
        self.db.refresh(income)
        return income

    def delete(self, income: Income) -> None:
        self.db.delete(income)
        self.db.commit()

    def summarize(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[Decimal, list[dict]]:
        q = (
            self.db.query(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.sum(Income.amount).label("total"),
            )
            .join(Category, Income.category_id == Category.id)
            .filter(Income.user_id == user_id)
        )

        if start_date:
            q = q.filter(Income.income_date >= start_date)
        if end_date:
            q = q.filter(Income.income_date <= end_date)

        rows = q.group_by(Category.id, Category.name).all()

        total = sum((r.total for r in rows), Decimal(0))
        by_category = [
            {"category_id": r.category_id, "category_name": r.category_name, "total": r.total}
            for r in rows
        ]
        return total, by_category
