from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryNested(BaseModel):
    id: int = Field(..., description="Category identifier.")
    name: str = Field(..., description="Category name.")

    model_config = ConfigDict(from_attributes=True)


class IncomeCreate(BaseModel):
    category_id: Optional[int] = Field(None, description="ID of the category this income belongs to. Omit or pass null to leave uncategorised.")
    description: str = Field(..., description="Short description of the income.")
    amount: Decimal = Field(..., description="Income amount (must be greater than 0).")
    income_date: date = Field(..., description="Date the income was received (YYYY-MM-DD).")

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_id": 2,
                "description": "Monthly salary",
                "amount": 3500.00,
                "income_date": "2026-06-01",
            }
        }
    )


class IncomeResponse(BaseModel):
    id: int = Field(..., description="Unique income identifier.")
    description: str = Field(..., description="Description of the income.")
    amount: Decimal = Field(..., description="Income amount.")
    income_date: date = Field(..., description="Date the income was received.")
    created_at: datetime = Field(..., description="UTC timestamp when the record was created.")
    category: Optional[CategoryNested] = Field(None, description="Category this income belongs to, if any.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "description": "Monthly salary",
                "amount": 3500.00,
                "income_date": "2026-06-01",
                "created_at": "2026-06-01T09:00:00",
                "category": None,
            }
        },
    )


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
    category_id: int = Field(..., description="Category identifier.")
    category_name: str = Field(..., description="Category name.")
    total: Decimal = Field(..., description="Total income amount in this category.")


class IncomeSummary(BaseModel):
    total_income: Decimal = Field(..., description="Total income received in the selected period.")
    by_category: list[IncomeCategorySummary] = Field(..., description="Breakdown of income by category.")
    period: str = Field(..., description="The period this summary covers.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_income": 4000.00,
                "by_category": [
                    {"category_id": 1, "category_name": "Salary", "total": 3500.00},
                    {"category_id": 2, "category_name": "Freelance", "total": 500.00},
                ],
                "period": "month",
            }
        }
    )
