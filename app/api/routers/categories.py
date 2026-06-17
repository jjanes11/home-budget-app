from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()

_ERROR = {"content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}}


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
    responses={409: {**_ERROR, "description": "Category name already exists"}},
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).create_category(user_id=current_user.id, name=payload.name)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).list_categories(user_id=current_user.id)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    responses={404: {**_ERROR, "description": "Category not found"}},
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).get_category(user_id=current_user.id, category_id=category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    responses={
        404: {**_ERROR, "description": "Category not found"},
        409: {**_ERROR, "description": "Category name already exists"},
    },
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CategoryService(db).update_category(
        user_id=current_user.id, category_id=category_id, name=payload.name
    )


@router.delete(
    "/{category_id}",
    status_code=204,
    responses={404: {**_ERROR, "description": "Category not found"}},
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    CategoryService(db).delete_category(user_id=current_user.id, category_id=category_id)
