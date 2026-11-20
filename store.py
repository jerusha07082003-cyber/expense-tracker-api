"""Data-access layer: all SQL lives here so the API layer stays thin and testable."""
import sqlite3
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      REAL    NOT NULL CHECK (amount > 0),
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    date        TEXT    NOT NULL            -- ISO format: YYYY-MM-DD
);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def create_expense(conn: sqlite3.Connection, data: dict) -> dict:
    cur = conn.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (data["amount"], data["category"], data["description"], data["date"]),
    )
    conn.commit()
    return get_expense(conn, cur.lastrowid)


def get_expense(conn: sqlite3.Connection, expense_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    return _row_to_dict(row)


def list_expenses(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category.strip().lower())
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM expenses {where} ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    rows = conn.execute(sql, (*params, limit, offset)).fetchall()
    return [dict(r) for r in rows]


def update_expense(conn: sqlite3.Connection, expense_id: int, data: dict) -> Optional[dict]:
    cur = conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, description = ?, date = ? WHERE id = ?",
        (data["amount"], data["category"], data["description"], data["date"], expense_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        return None
    return get_expense(conn, expense_id)


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cur.rowcount > 0


def summary_by_category(
    conn: sqlite3.Connection, start: Optional[str] = None, end: Optional[str] = None
) -> list[dict]:
    clauses, params = [], []
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        "SELECT category, ROUND(SUM(amount), 2) AS total, COUNT(*) AS count "
        f"FROM expenses {where} GROUP BY category ORDER BY total DESC"
    )
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
def total_expenses(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict:
    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category.strip().lower())
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total, COUNT(*) AS count FROM expenses {where}"
    return dict(conn.execute(sql, params).fetchone())