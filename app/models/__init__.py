# Import all models so SQLAlchemy metadata is fully populated before create_all()
from app.models.user import User  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.income import Income  # noqa: F401
