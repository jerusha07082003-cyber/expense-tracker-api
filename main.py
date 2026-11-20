"""FastAPI application. Run with:  uvicorn app.main:app --reload"""
import datetime as dt
import os
import sqlite3
from .schemas import CategorySummary, ExpenseIn, ExpenseOut, TotalOut
from typing import Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query

from . import store
from .schemas import CategorySummary, ExpenseIn, ExpenseOut

app = FastAPI(
    title="Expense Tracker API",
    version="1.0.0",
    description="A small REST API to record expenses and see spending by category.",
)


def get_conn() -> Iterator[sqlite3.Connection]:
    """One SQLite connection per request. DB path comes from the EXPENSE_DB env var."""
    conn = sqlite3.connect(os.environ.get("EXPENSE_DB", "expenses.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    store.init_db(conn)
    try:
        yield conn
    finally:
        conn.close()


def _check_range(start: Optional[dt.date], end: Optional[dt.date]) -> None:
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(expense: ExpenseIn, conn: sqlite3.Connection = Depends(get_conn)):
    return store.create_expense(conn, expense.model_dump(mode="json"))


@app.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(
    category: Optional[str] = None,
    start: Optional[dt.date] = None,
    end: Optional[dt.date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_conn),
):
    _check_range(start, end)
    return store.list_expenses(
        conn,
        category=category,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
        limit=limit,
        offset=offset,
    )

@app.get("/expenses/total", response_model=TotalOut)
def total_expenses(
    category: Optional[str] = None,
    start: Optional[dt.date] = None,
    end: Optional[dt.date] = None,
    conn: sqlite3.Connection = Depends(get_conn),
):
    _check_range(start, end)
    return store.total_expenses(
        conn,
        category=category,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )
@app.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    expense = store.get_expense(conn, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int, expense: ExpenseIn, conn: sqlite3.Connection = Depends(get_conn)
):
    updated = store.update_expense(conn, expense_id, expense.model_dump(mode="json"))
    if updated is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    if not store.delete_expense(conn, expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")


@app.get("/summary", response_model=list[CategorySummary])
def summary(
    start: Optional[dt.date] = None,
    end: Optional[dt.date] = None,
    conn: sqlite3.Connection = Depends(get_conn),
):
    _check_range(start, end)
    return store.summary_by_category(
        conn,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )
