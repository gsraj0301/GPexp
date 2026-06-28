from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ExpenseMonth:
    id: int
    year: int
    month: int
    is_closed: bool
    closed_at: Optional[datetime]
    created_at: datetime


@dataclass
class Expense:
    id: int
    month_id: int
    amount: float
    category: str
    note: str
    date: datetime
