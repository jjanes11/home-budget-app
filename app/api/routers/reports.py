from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter()


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

@router.get("/overview", response_model=OverviewResponse)
def overview(
    period: Literal["all_time", "month", "quarter", "year"] = Query(default="all_time"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_overview(
        user_id=current_user.id,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/by-category", response_model=ByCategoryResponse)
def by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_by_category(user_id=current_user.id)


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
def monthly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReportService(db).get_monthly_trend(user_id=current_user.id)
