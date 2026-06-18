"""
conftest.py — shared fixtures for integration tests.

Test database: home_budget_test on port 5433 (db_test Docker service).
Strategy: truncate all tables after each test (fast, avoids savepoint issues
          with some psycopg2 + SQLAlchemy combinations).
"""

import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ── point to the test DB before any app imports resolve settings ──────────────
# Use DATABASE_URL from the environment (set by CI) or fall back to the local
# Docker Compose test DB on port 5433.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/home_budget_test",
)

from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
import app.models  # noqa: F401, E402 — register all models with Base.metadata
from app.main import app as fastapi_app  # noqa: E402 — import after app.models to prevent rebinding

# ── engine / session pointing at the test DB ─────────────────────────────────
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once for the whole test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db(create_test_tables) -> Session:
    """
    Yield a DB session and truncate all tables afterwards so each test
    starts with a clean slate.
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Truncate in reverse dependency order
        with test_engine.connect() as conn:
            conn.execute(text(
                "TRUNCATE incomes, expenses, categories, users RESTART IDENTITY CASCADE"
            ))
            conn.commit()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """TestClient wired to use the test DB session."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


# ── factory helpers ───────────────────────────────────────────────────────────

def make_user(db: Session, email: str = "test@example.com", password: str = "password123"):
    from app.models.user import User
    from app.repositories.category_repository import CategoryRepository

    user = User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    CategoryRepository(db).seed_defaults(user.id)
    return user


def make_token(user) -> str:
    return create_access_token({"sub": str(user.id)})


def auth_headers_for(user) -> dict:
    return {"Authorization": f"Bearer {make_token(user)}"}


def make_category(db: Session, user, name: str = "TestCat") -> object:
    from app.models.category import Category

    cat = Category(user_id=user.id, name=name, is_default=False)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def make_expense(db: Session, user, category, amount: Decimal = Decimal("50.00"), description: str = "Test expense"):
    from app.models.expense import Expense

    exp = Expense(
        user_id=user.id,
        category_id=category.id,
        description=description,
        amount=amount,
        expense_date=date(2026, 1, 15),
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def make_income(db: Session, user, category=None, amount: Decimal = Decimal("1000.00"), description: str = "Salary"):
    from app.models.income import Income

    inc = Income(
        user_id=user.id,
        category_id=category.id if category else None,
        description=description,
        amount=amount,
        income_date=date(2026, 1, 10),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


# ── convenience fixtures ──────────────────────────────────────────────────────

@pytest.fixture()
def test_user(db: Session):
    return make_user(db)


@pytest.fixture()
def test_user2(db: Session):
    return make_user(db, email="other@example.com")


@pytest.fixture()
def headers(test_user) -> dict:
    return auth_headers_for(test_user)


@pytest.fixture()
def headers2(test_user2) -> dict:
    return auth_headers_for(test_user2)
