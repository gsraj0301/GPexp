# Architecture - Monthly Expense Tracker

## Overview

A lightweight mobile/desktop app for a single worker to track daily expenses on a monthly basis. Built with Flet (Python + Flutter), using SQLite for local storage. No server, no login.

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.11+ | Worker is familiar with Python (tkinter/Qt5) |
| UI Framework | Flet | Python-based, reactive UI, desktop dev → mobile deploy, no Android Studio needed |
| Storage | SQLite (via `sqlite3`) | Local-only, zero setup, lightweight |
| Packaging | Flet Cloud Build | Generates APK for Android without Android Studio on local machine |

---

## Data Model

```
┌─────────────────┐          ┌─────────────────┐
│   ExpenseMonth   │          │     Expense      │
├─────────────────┤          ├─────────────────┤
│ id (PK)         │◄─────────┤ id (PK)         │
│ year            │    1:N   │ month_id (FK)   │
│ month           │          │ amount           │
│ is_closed       │          │ category         │
│ closed_at       │          │ note             │
│ created_at      │          │ date             │
└─────────────────┘          └─────────────────┘
```

### ExpenseMonth
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `year` | INTEGER | Calendar year (e.g., 2026) |
| `month` | INTEGER | Calendar month (1-12) |
| `is_closed` | INTEGER | 0 = active, 1 = closed (paid) |
| `closed_at` | TEXT (ISO 8601) | Datetime when month was closed |
| `created_at` | TEXT (ISO 8601) | Datetime when month record was created |

### Expense
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `month_id` | INTEGER FK | References ExpenseMonth.id |
| `amount` | REAL | Expense amount (always positive) |
| `category` | TEXT | Predefined (Food/Transport/Materials/Other) or custom |
| `note` | TEXT | Optional user note |
| `date` | TEXT (ISO 8601) | Date the expense was incurred |

### Constraints
- Unique constraint on `(year, month)` in ExpenseMonth
- Cascade delete: deleting a month deletes all its expenses
- Amount must be > 0

---

## Application Flow

```
┌──────────────┐
│  App Launch   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Get or Create current month record │
│  (is_closed=0, year+month = now)    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│         Main Screen Loads           │
│  - Month header + History button     │
│  - Expense input form                │
│  - List of all expenses this month   │
│  - Total display + Close Month btn   │
└──────┬──────────────┬───────────────┘
       │              │
       ▼              ▼
  ┌────────┐    ┌──────────┐
  │Add Exp │    │Close Mo  │
  └───┬────┘    └────┬─────┘
      │              │
      ▼              ▼
  Save to        Confirm dialog
  SQLite         → Close month
  → Refresh      → Create next month
    list         → Refresh screen
```

---

## Component Tree (Flet Controls)

```
Page
├── AppBar ("June 2026" + History IconButton)
├── Column (main content, scrollable)
│   ├── Card: Expense Input Form
│   │   ├── Row
│   │   │   ├── TextField (amount, numeric keyboard)
│   │   │   ├── Dropdown (category: Food/Transport/Materials/Other/Custom)
│   │   │   └── IconButton (date picker)
│   │   ├── TextField (custom category, shown when "Custom" selected)
│   │   └── ElevatedButton ("✓ Save Expense")
│   │
│   ├── Divider
│   │
│   ├── Expense List (ListView / Column)
│   │   └── [for each expense]
│   │       Card
│   │       └── ListTile
│   │           ├── leading: date
│   │           ├── title: category
│   │           ├── subtitle: note (optional)
│   │           └── trailing: amount (₹)
│   │
│   └── Card: Footer
│       ├── Text ("Month Total: ₹xxx")
│       ├── OutlinedButton ("💰 Show Total")
│       └── FilledButton ("✅ Close Month")
│
└── Dialog (Total popup / Close Month confirmation / History)
```

---

## Screens

### 1. Main Screen (Current Month)
- Displays current active month (year-month that is not closed)
- Shows all expenses organized by date
- Input form for adding new expenses
- Footer with total and close actions

### 2. History Screen
- Dialog or separate view
- Lists all months (closed and current)
- Each row shows: month name, total, closed status
- Tap a row → expand/collapse expense details for that month

### 3. Total Dialog
- Shows computed sum of all expenses in current month
- Shows count of expenses
- Simple dismissable dialog

### 4. Close Month Dialog
- Confirmation: "Close June 2026? Make sure you've received payment."
- On confirm: sets `is_closed=1`, `closed_at=now`, creates new month record
- If next month already exists (unusual), just activates it

---

## Data Layer Architecture

```
┌──────────────────────────────┐
│         main.py               │
│  UI logic, event handlers     │
└────────────┬─────────────────┘
             │ calls
             ▼
┌──────────────────────────────┐
│        database.py            │
│  SQLite connection manager    │
│  CRUD operations              │
│  - get_active_month()         │
│  - create_month(year, month)  │
│  - close_month(month_id)      │
│  - add_expense(month_id, ...) │
│  - get_expenses(month_id)     │
│  - get_month_total(month_id)  │
│  - get_all_months()           │
│  - init_db()                  │
└────────────┬─────────────────┘
             │ uses
             ▼
┌──────────────────────────────┐
│       expenses.db (SQLite)    │
│  • expense_months table       │
│  • expenses table             │
└──────────────────────────────┘
```

---

## Directory Structure

```
expense_tracker/
├── main.py              # Entry point, Flet UI
├── database.py          # SQLite operations
├── models.py            # Dataclasses / NamedTuples
├── ARCHITECTURE.md      # This file
├── SPEC.md              # Task breakdown
└── expenses.db          # SQLite database (auto-created on first run)
```

---

## Key Design Decisions

1. **Month-based periods instead of custom periods** — payment is received at month end, so months are the natural boundary.

2. **Manual "Close Month" instead of automatic** — worker controls when a month is closed (after receiving payment), avoiding confusion.

3. **All expenses this month visible** — worker sees the full monthly picture, not just today's entries.

4. **SQLite over JSON** — structured queries, no loading entire file into memory, built-in aggregations (SUM), ACID compliance.

5. **No login / no cloud** — single user, single device. Simpler and faster.

6. **Flet over KivyMD** — more modern UI, easier deployment, reactive pattern, smaller binary.
