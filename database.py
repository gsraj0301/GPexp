import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from models import ExpenseMonth, Expense

DB_PATH = os.environ.get("FLET_APP_STORAGE_DATA", ".")
if os.path.isdir(DB_PATH):
    DB_PATH = os.path.join(DB_PATH, "expenses.db")
else:
    DB_PATH = os.path.join(".", "expenses.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expense_months (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            is_closed INTEGER NOT NULL DEFAULT 0,
            closed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(year, month)
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            note TEXT DEFAULT '',
            date TEXT NOT NULL,
            FOREIGN KEY (month_id) REFERENCES expense_months(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def _row_to_month(row: sqlite3.Row) -> ExpenseMonth:
    return ExpenseMonth(
        id=row["id"],
        year=row["year"],
        month=row["month"],
        is_closed=bool(row["is_closed"]),
        closed_at=_parse_datetime(row["closed_at"]),
        created_at=_parse_datetime(row["created_at"]),
    )


def _row_to_expense(row: sqlite3.Row) -> Expense:
    return Expense(
        id=row["id"],
        month_id=row["month_id"],
        amount=row["amount"],
        category=row["category"],
        note=row["note"],
        date=_parse_datetime(row["date"]),
    )


def _parse_datetime(val: Optional[str]) -> Optional[datetime]:
    if val is None:
        return None
    return datetime.fromisoformat(val)


# --- ExpenseMonth CRUD ---


def get_active_month(year: int, month: int) -> ExpenseMonth:
    conn = _get_conn()

    cur = conn.execute("SELECT * FROM expense_months WHERE is_closed = 0 LIMIT 1")
    row = cur.fetchone()
    if row:
        conn.close()
        return _row_to_month(row)

    cur = conn.execute(
        "SELECT * FROM expense_months ORDER BY year DESC, month DESC LIMIT 1"
    )
    last = cur.fetchone()
    if last:
        y, m = last["year"], last["month"]
        if y == year and m == month:
            next_year = year + (month // 12)
            next_month = (month % 12) + 1
        else:
            next_year, next_month = year, month
    else:
        next_year, next_month = year, month

    conn.execute(
        "INSERT INTO expense_months (year, month) VALUES (?, ?)",
        (next_year, next_month),
    )
    conn.commit()
    cur = conn.execute("SELECT * FROM expense_months WHERE id = last_insert_rowid()")
    row = cur.fetchone()
    conn.close()
    return _row_to_month(row)


def get_month(month_id: int) -> Optional[ExpenseMonth]:
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM expense_months WHERE id = ?", (month_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_month(row)


def get_all_months() -> List[Tuple[ExpenseMonth, float]]:
    conn = _get_conn()
    cur = conn.execute("""
        SELECT m.*, COALESCE(SUM(e.amount), 0) as total
        FROM expense_months m
        LEFT JOIN expenses e ON e.month_id = m.id
        GROUP BY m.id
        ORDER BY m.year DESC, m.month DESC
    """)
    rows = cur.fetchall()
    conn.close()
    result: List[Tuple[ExpenseMonth, float]] = []
    for row in rows:
        month = ExpenseMonth(
            id=row["id"],
            year=row["year"],
            month=row["month"],
            is_closed=bool(row["is_closed"]),
            closed_at=_parse_datetime(row["closed_at"]),
            created_at=_parse_datetime(row["created_at"]),
        )
        result.append((month, row["total"]))
    return result


def create_month(year: int, month: int) -> ExpenseMonth:
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM expense_months WHERE year = ? AND month = ?", (year, month))
    existing = cur.fetchone()
    if existing:
        if existing["is_closed"]:
            conn.execute(
                "UPDATE expense_months SET is_closed = 0, closed_at = NULL WHERE id = ?",
                (existing["id"],),
            )
            conn.commit()
            cur = conn.execute("SELECT * FROM expense_months WHERE id = ?", (existing["id"],))
            row = cur.fetchone()
            conn.close()
            return _row_to_month(row)
        conn.close()
        return _row_to_month(existing)

    conn.execute(
        "INSERT INTO expense_months (year, month) VALUES (?, ?)",
        (year, month),
    )
    conn.commit()
    cur = conn.execute("SELECT * FROM expense_months WHERE id = last_insert_rowid()")
    row = cur.fetchone()
    conn.close()
    return _row_to_month(row)


def close_month(month_id: int) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE expense_months SET is_closed = 1, closed_at = datetime('now','localtime') WHERE id = ?",
        (month_id,),
    )
    conn.commit()
    conn.close()


# --- Settings ---


def get_setting(key: str, default: str = "") -> str:
    conn = _get_conn()
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


# --- Expense CRUD ---


def add_expense(month_id: int, amount: float, category: str, note: str, date: str) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO expenses (month_id, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
        (month_id, amount, category, note, date),
    )
    conn.commit()
    expense_id = cur.lastrowid
    conn.close()
    return expense_id


def get_expenses(month_id: int) -> List[Expense]:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT * FROM expenses WHERE month_id = ? ORDER BY date DESC, id DESC",
        (month_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_expense(r) for r in rows]


def get_yesterday_expenses(month_id: int) -> List[Expense]:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    conn = _get_conn()
    cur = conn.execute(
        "SELECT * FROM expenses WHERE month_id = ? AND date = ? ORDER BY id",
        (month_id, yesterday),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_expense(r) for r in rows]


def get_month_total(month_id: int) -> float:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE month_id = ?",
        (month_id,),
    )
    result = cur.fetchone()[0]
    conn.close()
    return result
