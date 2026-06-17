from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class CategoryNested(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    category_id: int
    description: str
    amount: Decimal
    expense_date: date

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: Decimal
    expense_date: date
    created_at: datetime
    category: CategoryNested

    model_config = {"from_attributes": True}


class ExpenseFilters(BaseModel):
    category_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
    sort_by: Literal["created_at", "amount", "expense_date"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


class ExpenseSummary(BaseModel):
    total_spent: Decimal
    by_category: list[CategorySummary]
    period: str
