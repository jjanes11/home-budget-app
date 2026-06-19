from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 – registers all models with Base.metadata
from app.api.routers import auth as auth_router
from app.api.routers import categories as categories_router
from app.api.routers import expenses as expenses_router
from app.api.routers import incomes as incomes_router
from app.api.routers import reports as reports_router
from app.db.base import Base
from app.db.session import engine

_tags_metadata = [
    {
        "name": "Authentication",
        "description": (
            "Register a new account, log in to receive a JWT access token, "
            "and retrieve the current authenticated user."
        ),
    },
    {
        "name": "Categories",
        "description": "Manage expense and income categories owned by the authenticated user.",
    },
    {
        "name": "Expenses",
        "description": (
            "Create, list, filter, and delete personal expense records. "
            "Supports period-based summaries grouped by category."
        ),
    },
    {
        "name": "Income",
        "description": (
            "Create, list, filter, and delete personal income records. "
            "Supports period-based summaries grouped by category."
        ),
    },
    {
        "name": "Reporting",
        "description": (
            "Aggregated financial reports: balance overview with net income, "
            "breakdown by category, and month-by-month trend."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Home Budget API",
    description=(
        "A personal finance backend for tracking **expenses**, **income**, and **categories**.\n\n"
        "## Authentication\n\n"
        "All endpoints except `POST /auth/register` and `POST /auth/login` require a JWT bearer token.\n\n"
        "1. Register via `POST /auth/register`, then log in via `POST /auth/login`.\n"
        "2. Click **Authorize** (🔒), enter your email as **username** and your **password** — "
        "Swagger will call `/auth/login` and attach the token automatically.\n"
    ),
    version="1.0.0",
    license_info={"name": "MIT"},
    openapi_tags=_tags_metadata,
    lifespan=lifespan,
)

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(categories_router.router, prefix="/categories", tags=["Categories"])
app.include_router(expenses_router.router, prefix="/expenses", tags=["Expenses"])
app.include_router(incomes_router.router, prefix="/incomes", tags=["Income"])
app.include_router(reports_router.router, prefix="/reports", tags=["Reporting"])


@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}
