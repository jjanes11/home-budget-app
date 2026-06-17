from sqlalchemy.orm import Session

from app.models.category import Category

DEFAULT_CATEGORIES = [
    "Accommodation",
    "Entertainment",
    "Food",
    "Health",
    "Other",
    "Transport",
    "Utilities",
]


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int, category_id: int) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )

    def get_by_name(self, user_id: int, name: str) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id, Category.name == name)
            .first()
        )

    def list_by_user(self, user_id: int) -> list[Category]:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.name)
            .all()
        )

    def create(self, user_id: int, name: str, is_default: bool = False) -> Category:
        category = Category(user_id=user_id, name=name, is_default=is_default)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, name: str) -> Category:
        category.name = name
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

    def seed_defaults(self, user_id: int) -> None:
        existing = {c.name for c in self.list_by_user(user_id)}
        new_categories = [
            Category(user_id=user_id, name=name, is_default=True)
            for name in DEFAULT_CATEGORIES
            if name not in existing
        ]
        if new_categories:
            self.db.add_all(new_categories)
            self.db.commit()
