from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.expense import ExpenseCreate, ExpenseFilters, ExpenseResponse, ExpenseSummary
from app.services.expense_service import ExpenseService

router = APIRouter()

_401 = {"model": ErrorResponse, "description": "Missing, invalid, or expired token."}
_404 = {"model": ErrorResponse, "description": "Expense not found."}


@router.post(
    "",
    summary="Create an expense",
    description="Record a new expense for the authenticated user. The category must belong to the user.",
    operation_id="createExpense",
    response_model=ExpenseResponse,
    status_code=201,
    responses={
        401: _401,
        404: {"model": ErrorResponse, "description": "Category not found."},
    },
)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ExpenseService(db).create_expense(user_id=current_user.id, data=payload)


@router.get(
    "/summary",
    summary="Get expense summary",
    description=(
        "Return the total amount spent and a per-category breakdown for the given period. "
        "Periods: `all_time`, `week` (last 7 days), `month` (current calendar month), `year` (current year)."
    ),
    operation_id="getExpenseSummary",
    response_model=ExpenseSummary,
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
    return ExpenseService(db).get_summary(user_id=current_user.id, period=period)


@router.get(
    "",
    summary="List expenses",
    description="Return a filtered and sorted list of the authenticated user's expenses.",
    operation_id="listExpenses",
    response_model=list[ExpenseResponse],
    responses={401: _401},
)
def list_expenses(
    category_id: Annotated[Optional[int], Query(description="Filter by category ID.")] = None,
    min_amount: Annotated[Optional[float], Query(description="Minimum expense amount (inclusive).")] = None,
    max_amount: Annotated[Optional[float], Query(description="Maximum expense amount (inclusive).")] = None,
    start_date: Annotated[Optional[str], Query(description="Include expenses on or after this date (YYYY-MM-DD).", examples=["2026-06-01"])] = None,
    end_date: Annotated[Optional[str], Query(description="Include expenses on or before this date (YYYY-MM-DD).", examples=["2026-06-30"])] = None,
    search: Annotated[Optional[str], Query(description="Case-insensitive search in expense description.")] = None,
    sort_by: Annotated[Literal["created_at", "amount", "expense_date"], Query(description="Field to sort results by.")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort direction.")] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date
    from decimal import Decimal

    filters = ExpenseFilters(
        category_id=category_id,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        start_date=date.fromisoformat(start_date) if start_date else None,
        end_date=date.fromisoformat(end_date) if end_date else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ExpenseService(db).get_expenses_filtered(user_id=current_user.id, filters=filters)


@router.get(
    "/{expense_id}",
    summary="Get an expense",
    description="Return a single expense record by its ID.",
    operation_id="getExpense",
    response_model=ExpenseResponse,
    responses={401: _401, 404: _404},
)
def get_expense(
    expense_id: Annotated[int, Path(description="Unique identifier of the expense.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ExpenseService(db).get_expense_by_id(user_id=current_user.id, expense_id=expense_id)


@router.delete(
    "/{expense_id}",
    summary="Delete an expense",
    description="Permanently delete an expense record.",
    operation_id="deleteExpense",
    status_code=204,
    responses={401: _401, 404: _404},
)
def delete_expense(
    expense_id: Annotated[int, Path(description="Unique identifier of the expense to delete.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ExpenseService(db).delete_expense(user_id=current_user.id, expense_id=expense_id)
