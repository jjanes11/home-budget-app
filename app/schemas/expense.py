from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryNested(BaseModel):
    id: int = Field(..., description="Category identifier.")
    name: str = Field(..., description="Category name.")

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(BaseModel):
    category_id: int = Field(..., description="ID of the category this expense belongs to.")
    description: str = Field(..., description="Short description of the expense.")
    amount: Decimal = Field(..., description="Expense amount (must be greater than 0).")
    expense_date: date = Field(..., description="Date of the expense (YYYY-MM-DD).")

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_id": 3,
                "description": "Groceries",
                "amount": 42.50,
                "expense_date": "2026-06-18",
            }
        }
    )


class ExpenseResponse(BaseModel):
    id: int = Field(..., description="Unique expense identifier.")
    description: str = Field(..., description="Description of the expense.")
    amount: Decimal = Field(..., description="Expense amount.")
    expense_date: date = Field(..., description="Date of the expense.")
    created_at: datetime = Field(..., description="UTC timestamp when the record was created.")
    category: CategoryNested = Field(..., description="Category this expense belongs to.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "description": "Groceries",
                "amount": 42.50,
                "expense_date": "2026-06-18",
                "created_at": "2026-06-18T12:00:00",
                "category": {"id": 3, "name": "Food"},
            }
        },
    )


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
    category_id: int = Field(..., description="Category identifier.")
    category_name: str = Field(..., description="Category name.")
    total: Decimal = Field(..., description="Total amount spent in this category.")


class ExpenseSummary(BaseModel):
    total_spent: Decimal = Field(..., description="Total amount spent in the selected period.")
    by_category: list[CategorySummary] = Field(..., description="Breakdown of spending by category.")
    period: str = Field(..., description="The period this summary covers.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_spent": 320.00,
                "by_category": [
                    {"category_id": 3, "category_name": "Food", "total": 180.00},
                    {"category_id": 5, "category_name": "Transport", "total": 140.00},
                ],
                "period": "month",
            }
        }
    )
