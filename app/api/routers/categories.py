from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.errors import ErrorResponse
from app.services.category_service import CategoryService

router = APIRouter()

_401 = {"model": ErrorResponse, "description": "Missing, invalid, or expired token."}
_404 = {"model": ErrorResponse, "description": "Category not found."}
_409 = {"model": ErrorResponse, "description": "A category with this name already exists."}


@router.post(
    "",
    summary="Create a category",
    description="Create a new expense/income category for the authenticated user. Names are normalised to title case.",
    operation_id="createCategory",
    response_model=CategoryResponse,
    status_code=201,
    responses={401: _401, 409: _409},
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).create_category(user_id=current_user.id, name=payload.name)


@router.get(
    "",
    summary="List categories",
    description="Return all categories belonging to the authenticated user.",
    operation_id="listCategories",
    response_model=list[CategoryResponse],
    responses={401: _401},
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).list_categories(user_id=current_user.id)


@router.get(
    "/{category_id}",
    summary="Get a category",
    description="Return a single category by its ID.",
    operation_id="getCategory",
    response_model=CategoryResponse,
    responses={401: _401, 404: _404},
)
def get_category(
    category_id: Annotated[int, Path(description="Unique identifier of the category.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).get_category(user_id=current_user.id, category_id=category_id)


@router.put(
    "/{category_id}",
    summary="Update a category",
    description="Rename an existing category. The new name is normalised to title case.",
    operation_id="updateCategory",
    response_model=CategoryResponse,
    responses={401: _401, 404: _404, 409: _409},
)
def update_category(
    category_id: Annotated[int, Path(description="Unique identifier of the category to update.")],
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).update_category(
        user_id=current_user.id, category_id=category_id, name=payload.name
    )


@router.delete(
    "/{category_id}",
    summary="Delete a category",
    description="Permanently delete a category. Associated expenses and incomes are also deleted (cascade).",
    operation_id="deleteCategory",
    status_code=204,
    responses={401: _401, 404: _404},
)
def delete_category(
    category_id: Annotated[int, Path(description="Unique identifier of the category to delete.")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    CategoryService(db).delete_category(user_id=current_user.id, category_id=category_id)
