from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.repo = CategoryRepository(db)

    def seed_default_categories(self, user_id: int) -> None:
        self.repo.seed_defaults(user_id)

    def create_category(self, user_id: int, name: str) -> Category:
        normalized = name.strip().title()
        if self.repo.get_by_name(user_id, normalized):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists",
            )
        return self.repo.create(user_id=user_id, name=normalized)

    def list_categories(self, user_id: int) -> list[Category]:
        return self.repo.list_by_user(user_id)

    def get_category(self, user_id: int, category_id: int) -> Category:
        category = self.repo.get_by_id(user_id, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category

    def update_category(self, user_id: int, category_id: int, name: str) -> Category:
        normalized = name.strip().title()
        category = self.get_category(user_id, category_id)
        existing = self.repo.get_by_name(user_id, normalized)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists",
            )
        return self.repo.update(category, normalized)

    def delete_category(self, user_id: int, category_id: int) -> None:
        category = self.get_category(user_id, category_id)
        self.repo.delete(category)
