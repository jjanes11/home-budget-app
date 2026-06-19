from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.services.report_service import ReportService

router = APIRouter()

_401 = {"model": ErrorResponse, "description": "Missing, invalid, or expired token."}


# --- inline response schemas ---

class OverviewResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    period: str


class CategoryTotalItem(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


class ByCategoryResponse(BaseModel):
    expenses_by_category: list[CategoryTotalItem]
    income_by_category: list[CategoryTotalItem]


class MonthlyTrendItem(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


# --- endpoints ---

@router.get(
    "/overview",
    summary="Financial overview",
    description=(
        "Return total income, total expenses, and net balance for the given period. "
        "Use `start_date` and `end_date` to override the period with a custom date range."
    ),
    operation_id="getOverview",
    response_model=OverviewResponse,
    responses={401: _401},
)
def overview(
    period: Annotated[
        Literal["all_time", "month", "quarter", "year"],
        Query(description="Predefined time period. Ignored when start_date or end_date is provided."),
    ] = "all_time",
    start_date: Annotated[Optional[date], Query(description="Custom range start date (YYYY-MM-DD). Overrides period.", examples=["2026-01-01"])] = None,
    end_date: Annotated[Optional[date], Query(description="Custom range end date (YYYY-MM-DD). Overrides period.", examples=["2026-06-30"])] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_overview(
        user_id=current_user.id,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/by-category",
    summary="Breakdown by category",
    description="Return total expenses and total income grouped by category across all time.",
    operation_id="getByCategory",
    response_model=ByCategoryResponse,
    responses={401: _401},
)
def by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_by_category(user_id=current_user.id)


@router.get(
    "/monthly-trend",
    summary="Monthly income vs expenses trend",
    description="Return a month-by-month breakdown of income, expenses, and net balance for all available data.",
    operation_id="getMonthlyTrend",
    response_model=list[MonthlyTrendItem],
    responses={401: _401},
)
def monthly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_monthly_trend(user_id=current_user.id)
