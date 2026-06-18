# Home Budget API

A personal finance backend system for tracking expenses, income, and categories — built with FastAPI and PostgreSQL.

## Features

- **Authentication** — JWT-based registration and login
- **Expenses** — create, filter, and summarize personal expenses
- **Income** — track income entries by category and date
- **Categories** — user-owned categories shared across expenses and income
- **Reporting** — period-based summaries (week, month, year, all-time)

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### 1. Start services

```bash
docker compose up --build
```

This starts two services:
- `api` — FastAPI application on port `8000`
- `db` — PostgreSQL 16 on port `5432`

### 2. Explore the API

Open the interactive docs in your browser:

```
http://localhost:8000/docs
```

---

## Running Tests

### Unit tests (no database required)

```bash
pytest tests/unit/ -v
```

Runs in under a second — no Docker, no PostgreSQL needed.

### Integration tests

Require the `db_test` service (PostgreSQL on port `5433`):

```bash
# Start the test database
docker compose up db_test -d

# Run integration tests
pytest tests/integration/ -q
```

### Full suite

```bash
docker compose up db_test -d
pytest -q
```

Integration tests use a real PostgreSQL database. All tables are truncated between tests for isolation.

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Containerization | Docker / Docker Compose |
| Testing | Pytest + HTTPX |
| Linting | Ruff |

---

## Project Structure

```
app/
├── api/
│   └── routers/        # Route handlers (auth, expenses, incomes, categories, reports)
├── services/           # Business logic layer
├── repositories/       # Database access layer
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── core/               # Config and security utilities
└── db/                 # Database engine and session management
tests/
├── unit/               # Unit tests — service logic, no DB required
└── integration/        # Integration tests — real PostgreSQL
```

---

## CI/CD

GitHub Actions runs on every push to `main`/`develop` and on pull requests to `main`:

1. **Lint** — `ruff check .`
2. **Unit tests** — `pytest tests/unit/ -v` (no database needed)
3. **Integration tests** — `pytest -q` against a real PostgreSQL service container

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the full pipeline definition.

---

## Architecture

For a deeper look at the system design, layers, auth flow, and data flow:

> See [ARCHITECTURE.md](ARCHITECTURE.md)
