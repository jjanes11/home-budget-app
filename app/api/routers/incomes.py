from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeFilters, IncomeResponse, IncomeSummary
from app.services.income_service import IncomeService

router = APIRouter()

_ERROR = {"content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}}


@router.post(
    "",
    response_model=IncomeResponse,
    status_code=201,
    responses={404: {**_ERROR, "description": "Category not found"}},
)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).create_income(user_id=current_user.id, data=payload)


@router.get("/summary", response_model=IncomeSummary)
def get_summary(
    period: Literal["all_time", "week", "month", "year"] = Query(default="all_time"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).get_income_summary(user_id=current_user.id, period=period)


@router.get("", response_model=list[IncomeResponse])
def list_incomes(
    category_id: Optional[int] = Query(default=None),
    min_amount: Optional[float] = Query(default=None),
    max_amount: Optional[float] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: Literal["created_at", "amount", "income_date"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = IncomeFilters(
        category_id=category_id,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        start_date=date.fromisoformat(start_date) if start_date else None,
        end_date=date.fromisoformat(end_date) if end_date else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return IncomeService(db).get_income_filtered(user_id=current_user.id, filters=filters)


@router.get(
    "/{income_id}",
    response_model=IncomeResponse,
    responses={404: {**_ERROR, "description": "Income not found"}},
)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).get_income_by_id(user_id=current_user.id, income_id=income_id)


@router.delete(
    "/{income_id}",
    status_code=204,
    responses={404: {**_ERROR, "description": "Income not found"}},
)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    IncomeService(db).delete_income(user_id=current_user.id, income_id=income_id)
