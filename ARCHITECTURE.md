# Architecture — Home Budget API

## System Overview

A layered FastAPI backend backed by PostgreSQL. The application follows a strict three-layer separation: API → Service → Repository. Each layer has a single responsibility and communicates only with the layer directly below it.

```
Client
  │
  ▼
FastAPI (routers)       ← HTTP request/response, auth guards, schema validation
  │
  ▼
Service layer           ← business logic, authorization checks, error raising
  │
  ▼
Repository layer        ← SQL queries via SQLAlchemy 2.0 ORM
  │
  ▼
PostgreSQL 16
```

---

## Core Layers

### API Layer (`app/api/routers/`)

- One router module per domain: `auth`, `expenses`, `incomes`, `categories`, `reports`
- Handles HTTP concerns only: path parameters, query parameters, request bodies, status codes
- Injects the current authenticated user via a shared `deps.py` dependency
- Returns Pydantic response schemas; never returns raw ORM objects

### Service Layer (`app/services/`)

- Contains all business logic: validation rules, period calculations, category ownership checks
- Raises `HTTPException` when invariants are violated (e.g., category not owned by user)
- Calls one or more repositories; orchestrates cross-repository operations for reports

### Repository Layer (`app/repositories/`)

- Thin wrappers around SQLAlchemy `Session`
- No business logic — only CRUD and filtered queries
- Methods accept primitive arguments and return ORM model instances

---

## Domain Model

| Entity | Key fields | Relationships |
|---|---|---|
| `User` | `id`, `email`, `hashed_password`, `created_at` | owns Expenses, Incomes, Categories |
| `Category` | `id`, `name`, `user_id` | belongs to User; referenced by Expenses and Incomes |
| `Expense` | `id`, `amount`, `description`, `expense_date`, `user_id`, `category_id` | belongs to User and Category |
| `Income` | `id`, `amount`, `description`, `income_date`, `user_id`, `category_id` | belongs to User and Category |

All financial records are user-scoped — queries always filter by `user_id` so users never see each other's data.

---

## Authentication Flow

The API uses **OAuth2 password flow** with **JWT bearer tokens**.

```
POST /auth/register  →  hash password, persist User, return access token
POST /auth/login     →  verify password, issue JWT (HS256, 30-min expiry)

Subsequent requests:
  Authorization: Bearer <token>
    │
    ▼
  deps.get_current_user()  →  decode JWT → load User from DB → inject into route
```

Tokens are stateless — there is no session store or token revocation mechanism.

---

## Data Flow Example

A typical authenticated write request:

```
POST /expenses
  │  Authorization: Bearer <token>
  │  Body: { amount, description, category_id, expense_date }
  │
  ▼
expenses router
  ├─ validate request body (Pydantic)
  ├─ resolve current user (JWT dependency)
  └─ call ExpenseService.create_expense(user_id, data)
       │
       ▼
     ExpenseService
       ├─ verify category belongs to user (CategoryRepository.get_by_id)
       └─ call ExpenseRepository.create(...)
            │
            ▼
          SQLAlchemy INSERT → PostgreSQL
            │
            ▼
          ORM Expense instance returned up the stack
            │
            ▼
router returns ExpenseResponse (Pydantic schema)  →  201 Created
```

---

## Testing Strategy

The test suite is split into two tiers:

### Unit tests (`tests/unit/`)

- **Target**: service layer business logic (`ExpenseService`, `IncomeService`, `ReportService`) and the `_date_range` pure function in `report_service`
- **Isolation**: all repository and `Session` dependencies replaced with `MagicMock`; `date.today()` patched for deterministic date-range assertions
- **Speed**: ~0.35 s; no database, no Docker
- **54 tests** covering: 404 guards, argument delegation, period→start_date mapping, net balance calculation, monthly trend merging and zero-defaults

### Integration tests (`tests/integration/`)

- **No mocks** — every test hits a real PostgreSQL instance (`home_budget_test` on port 5433)
- **Fixture scope**: tables are created once per session; rows are truncated after each test via `TRUNCATE ... RESTART IDENTITY CASCADE`
- **HTTP layer tested end-to-end** using FastAPI's `TestClient` (backed by HTTPX)

### CI

GitHub Actions runs on every push/PR: `ruff check .` → unit tests → integration tests against a PostgreSQL 16 service container.
