from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


class CategoryNested(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class IncomeCreate(BaseModel):
    category_id: Optional[int] = None
    description: str
    amount: Decimal
    income_date: date

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class IncomeResponse(BaseModel):
    id: int
    description: str
    amount: Decimal
    income_date: date
    created_at: datetime
    category: Optional[CategoryNested] = None

    model_config = {"from_attributes": True}


class IncomeFilters(BaseModel):
    category_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class IncomeCategorySummary(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


class IncomeSummary(BaseModel):
    total_income: Decimal
    by_category: list[IncomeCategorySummary]
    period: str
