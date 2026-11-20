# Expense Tracker API

A small REST API for recording personal expenses and seeing where the money goes.
Built with **FastAPI**, **SQLite** and **pytest/unittest**, with a GitHub Actions workflow that runs the tests on every push.

## Problem statement

People track spending in notes apps or spreadsheets, which makes it hard to filter by date or category
and impossible for other apps to reuse the data. This project provides a validated, documented API
that any web or mobile front end can call to create, query and summarize expenses.

## Features

- Full CRUD for expenses (`POST/GET/PUT/DELETE /expenses`)
- Filtering by category and date range, with pagination (`limit`, `offset`)
- Spending summary per category (`GET /summary`)
- Input validation (positive amounts, real dates, no blank categories) with clear `422` errors
- Auto-generated OpenAPI spec and interactive docs at `/docs`
- Layered design: `schemas.py` (validation) / `main.py` (HTTP) / `store.py` (SQL)
- Tests for the data layer and the HTTP layer; CI on every push

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try every endpoint in the browser.

```bash
# create an expense
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 450, "category": "Food", "description": "Team lunch", "date": "2026-11-12"}'

# list food expenses in November
curl "http://127.0.0.1:8000/expenses?category=food&start=2026-11-01&end=2026-11-30"

# spending by category
curl http://127.0.0.1:8000/summary
```

## Run the tests

```bash
python -m pytest -v
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/expenses` | Create an expense |
| GET | `/expenses` | List with filters: `category`, `start`, `end`, `limit`, `offset` |
| GET | `/expenses/{id}` | Fetch one |
| PUT | `/expenses/{id}` | Replace one |
| DELETE | `/expenses/{id}` | Delete one |
| GET | `/summary` | Total and count per category, optional date range |
| GET | `/health` | Liveness check |

## Design decisions (good interview talking points)

- **Validation at the edge.** Pydantic rejects bad input before it reaches the database, and the table also has a `CHECK (amount > 0)` constraint as a second safety net.
- **SQL in one module.** `store.py` uses parameterized queries only (no string-built values), which prevents SQL injection and makes the logic testable without HTTP.
- **One connection per request,** opened and closed in a FastAPI dependency. Simple and safe for SQLite.
- **Dates stored as ISO strings** so range filters work with plain string comparison.

## Ideas to extend

- User accounts and JWT authentication
- Monthly budgets with an alert endpoint
- Swap SQLite for PostgreSQL using SQLAlchemy
- Dockerfile and deploy to a free host
