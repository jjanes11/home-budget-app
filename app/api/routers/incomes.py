from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.income import IncomeCreate, IncomeFilters, IncomeResponse, IncomeSummary
from app.services.income_service import IncomeService

router = APIRouter()

_401 = {"model": ErrorResponse, "description": "Missing, invalid, or expired token."}
_404 = {"model": ErrorResponse, "description": "Income not found."}


@router.post(
    "",
    summary="Create an income entry",
    description="Record a new income entry for the authenticated user. Category is optional.",
    operation_id="createIncome",
    response_model=IncomeResponse,
    status_code=201,
    responses={
        401: _401,
        404: {"model": ErrorResponse, "description": "Category not found."},
    },
)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).create_income(user_id=current_user.id, data=payload)


@router.get(
    "/summary",
    summary="Get income summary",
    description=(
        "Return the total income and a per-category breakdown for the given period. "
        "Periods: `all_time`, `week` (last 7 days), `month` (current calendar month), `year` (current year)."
    ),
    operation_id="getIncomeSummary",
    response_model=IncomeSummary,
    responses={401: _401},
)
def get_summary(
    period: Annotated[
        Literal["all_time", "week", "month", "year"],
        Query(description="Time period for the summary."),
    ] = "all_time",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).get_income_summary(user_id=current_user.id, period=period)


@router.get(
    "",
    summary="List income entries",
    description="Return a filtered and sorted list of the authenticated user's income entries.",
    operation_id="listIncomes",
    response_model=list[IncomeResponse],
    responses={401: _401},
)
def list_incomes(
    category_id: Annotated[Optional[int], Query(description="Filter by category ID.")] = None,
    min_amount: Annotated[Optional[float], Query(description="Minimum income amount (inclusive).")] = None,
    max_amount: Annotated[Optional[float], Query(description="Maximum income amount (inclusive).")] = None,
    start_date: Annotated[Optional[str], Query(description="Include entries on or after this date (YYYY-MM-DD).", examples=["2026-06-01"])] = None,
    end_date: Annotated[Optional[str], Query(description="Include entries on or before this date (YYYY-MM-DD).", examples=["2026-06-30"])] = None,
    search: Annotated[Optional[str], Query(description="Case-insensitive search in income description.")] = None,
    sort_by: Annotated[Literal["created_at", "amount", "income_date"], Query(description="Field to sort results by.")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort direction.")] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date
    from decimal import Decimal

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
    summary="Get an income entry",
    description="Return a single income record by its ID.",
    operation_id="getIncome",
    response_model=IncomeResponse,
    responses={401: _401, 404: _404},
)
def get_income(
    income_id: Annotated[int, Path(description="Unique identifier of the income entry.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return IncomeService(db).get_income_by_id(user_id=current_user.id, income_id=income_id)


@router.delete(
    "/{income_id}",
    summary="Delete an income entry",
    description="Permanently delete an income record.",
    operation_id="deleteIncome",
    status_code=204,
    responses={401: _401, 404: _404},
)
def delete_income(
    income_id: Annotated[int, Path(description="Unique identifier of the income entry to delete.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    IncomeService(db).delete_income(user_id=current_user.id, income_id=income_id)
