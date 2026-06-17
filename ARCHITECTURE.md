# Home Budget API – Architecture & Implementation Plan

## 1. Overview

This is a Home Budget REST API built with FastAPI and PostgreSQL.

It allows users to:
- Register and authenticate
- Manage categories (including predefined system categories)
- Track expenses (money spent)
- Track income (money earned)
- Filter and search financial records
- Generate aggregated financial reports

The system focuses on clean REST design, relational modeling, authentication, filtering, and SQL aggregation.

---

## 2. Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (ORM)
- Pydantic v2
- passlib[bcrypt]
- python-jose (JWT)
- pytest
- Docker + Docker Compose
- GitHub Actions (CI)

---

## 3. High-Level Architecture


Client (Postman / future SPA)
|
v
FastAPI Application
|
|-- API Layer (routers)
|-- Service Layer (business logic)
|-- Repository Layer (database access)
|
v
PostgreSQL Database


---

## 4. Project Structure


app/
│
├── main.py
│
├── core/
│ ├── config.py
│ ├── security.py
│
├── db/
│ ├── session.py
│ ├── base.py
│
├── models/
│ ├── user.py
│ ├── category.py
│ ├── expense.py
│ ├── income.py
│
├── schemas/
│ ├── user.py
│ ├── category.py
│ ├── expense.py
│ ├── income.py
│ ├── auth.py
│
├── repositories/
│ ├── expense_repository.py
│ ├── income_repository.py
│ ├── category_repository.py
│ ├── user_repository.py
│
├── services/
│ ├── auth_service.py
│ ├── expense_service.py
│ ├── income_service.py
│ ├── category_service.py
│ ├── report_service.py
│
├── api/
│ ├── routers/
│ │ ├── auth.py
│ │ ├── categories.py
│ │ ├── expenses.py
│ │ ├── incomes.py
│ │ ├── reports.py
│ │
│ ├── deps.py
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md


---

## 5. Data Model

### 5.1 User
- id
- email (unique)
- hashed_password
- balance (optional initial budget reference)
- created_at
- updated_at

---

### 5.2 Category
Supports:
- system default categories (Food, Transport, etc.)
- user-defined categories

Fields:
- id
- name
- user_id (nullable for system categories)
- is_default (bool)

---

### 5.3 Expense (money spent)
- id
- description
- amount (Decimal > 0)
- expense_date (business date)
- created_at
- updated_at
- user_id (FK → User)
- category_id (FK → Category)

---

### 5.4 Income (money earned)
- id
- description
- amount (Decimal > 0)
- income_date (business date)
- created_at
- updated_at
- user_id (FK → User)

---

## 6. Authentication Flow

- Passwords hashed using bcrypt (passlib)
- JWT tokens generated using python-jose
- OAuth2PasswordBearer used for authentication
- Current user resolved via dependency injection

---

## 7. API Endpoints

### 7.1 Auth
- POST /auth/register
- POST /auth/login
- GET /auth/me

---

### 7.2 Categories
- POST /categories
- GET /categories
- GET /categories/{id}
- PUT /categories/{id}
- DELETE /categories/{id}

Default categories are seeded on application startup.

---

## 7.3 Expenses

### CRUD
- POST /expenses
- GET /expenses
- GET /expenses/{id}
- PUT /expenses/{id}
- DELETE /expenses/{id}

---

### Filtering / Search / Sorting / Pagination

All filters are implemented using a **Pydantic filter dependency model**.

Supported query parameters:

#### Filtering
- category_id
- min_amount
- max_amount
- date_from
- date_to

#### Search
- search (case-insensitive search on description using `ILIKE`)

#### Sorting
- sort=amount_asc
- sort=amount_desc
- sort=date_asc
- sort=date_desc

#### Pagination
- page
- page_size

---

### Query Execution Flow

The query is built incrementally:

1. Base query (user-scoped)
2. Apply filters (if present)
3. Apply search (ILIKE on description)
4. Apply sorting (ORDER BY mapped fields)
5. Apply pagination (LIMIT/OFFSET)

---

## 7.4 Incomes

Same structure as expenses:

- POST /incomes
- GET /incomes
- GET /incomes/{id}
- PUT /incomes/{id}
- DELETE /incomes/{id}

Supports filtering, search, sorting, and pagination (same pattern as expenses).

---

## 7.5 Reports

### Endpoints
- GET /reports/summary?period=month|quarter|year
- GET /reports/summary?from=YYYY-MM-DD&to=YYYY-MM-DD

---

### Aggregation Features

Reports operate on aggregated SQL queries:

#### Total income
```sql
SUM(incomes.amount)
Total expenses
SUM(expenses.amount)
Net balance
net = total_income - total_expenses
Expenses grouped by category
GROUP BY category_id
SUM(amount)
Example response
{
  "period": "month",
  "total_income": 3000,
  "total_expenses": 1200,
  "net_balance": 1800,
  "expense_by_category": [
    { "category": "Food", "amount": 450 },
    { "category": "Transport", "amount": 200 }
  ]
}
8. Business Rules
Users can only access their own data (strict multi-tenancy)
Expense amounts must be > 0
Income amounts must be > 0
Categories:
system categories are global and read-only
user categories are editable
Expenses must belong to a category
All queries are scoped by authenticated user
9. Query Design Pattern

All list endpoints follow this pipeline:

Base Query
  → Filters (exact match conditions)
  → Search (ILIKE text search)
  → Sorting (ORDER BY mapped fields)
  → Pagination (LIMIT/OFFSET)

Grouping is only used in reporting endpoints.

10. Database Strategy
SQLAlchemy ORM models
No Alembic (simplified take-home setup)
Tables created on startup:
Base.metadata.create_all(bind=engine)

Optional:

seed default categories on startup
11. Docker Setup

Services:

FastAPI backend
PostgreSQL database

Run:

docker compose up --build
12. Testing Strategy

Using pytest + FastAPI TestClient.

Coverage:

Auth (register/login/me)
Categories CRUD + ownership rules
Expenses CRUD + filtering/sorting/search
Incomes CRUD + filtering
Reports aggregation correctness
13. CI Pipeline (GitHub Actions)

On push / pull request:

install dependencies
start PostgreSQL
run pytest

No deployment step included.

14. Non-Goals
No frontend implementation
No microservices architecture
No caching layer (Redis)
No event-driven system
No external FX or banking APIs
No overengineering of financial accounting systems
15. Implementation Order
Project setup + DB config
Auth system
Categories CRUD + seed data
Expenses CRUD + filtering system
Incomes CRUD
Reports aggregation
Tests
Docker setup
CI pipeline
16. Success Criteria

Project is complete when:

docker compose up runs everything
Swagger UI works (/docs)
Users can authenticate
Expenses + incomes CRUD works
Filtering, search, sorting work correctly
Reports return correct aggregates
Tests pass in CI

---
