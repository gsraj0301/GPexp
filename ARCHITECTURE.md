# Architecture - Monthly Expense Tracker

## Overview

A lightweight mobile/desktop app for a single worker to track daily expenses on a monthly basis. Built with Flet (Python + Flutter), using SQLite for local storage. No server, no login.

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.12 | Worker is familiar with Python (tkinter/Qt5) |
| UI Framework | Flet 0.85.3 | Python-based, reactive UI, desktop dev → mobile deploy |
| Storage | SQLite (via `sqlite3`) | Local-only, zero setup, lightweight |
| Packaging | GitHub Actions → APK | Automates build on push/trigger |
| Background Tasks | WorkManager (Dart) | Daily WhatsApp summary at 8 AM |
| Share Intent | share_plus (Dart) | Opens WhatsApp via Android share sheet |

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
| `category` | TEXT | Predefined (Tea/Water/Biscuit/Snack/Transport/Cartoon/Petrol) or custom |
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
Page (Stack)
├── AppBar ("June 2026" + History + Settings IconButtons)
│
├── Main Body (visible by default)
│   ├── Card: Expense Input Form
│   │   ├── Row
│   │   │   ├── TextField (amount, numeric keyboard)
│   │   │   └── Dropdown (category: Tea/Water/Biscuit/Snack/Transport/Cartoon/Petrol)
│   │   ├── TextField (custom category, always visible)
│   │   └── Row
│   │       ├── IconButton (date picker)
│   │       ├── Text (selected date)
│   │       └── FilledButton ("✓ Save")
│   │
│   ├── Divider
│   │
│   ├── Expense List (Column)
│   │   ├── Date header ("Jun 29, 2026")
│   │   │   └── [for each expense]
│   │   │       ListTile (category + amount ₹)
│   │   └── (or "No expenses yet" empty state)
│   │
│   ├── Divider
│   │
│   ├── Text ("Month Total: ₹xxx")
│   └── Row
│       ├── OutlinedButton ("Show Total")
│       └── FilledButton ("Close Month")
│
├── History View (hidden)
│   └── Column
│       └── [for each month]
│           Card → tap → AlertDialog with expense list
│
└── Settings View (hidden)
    └── Card
        ├── Text ("WhatsApp Daily Summary")
        ├── Switch (enable/disable)
        ├── Divider
        └── OutlinedButton ("Send Yesterday's Now")

Dialogs: AlertDialog (Save success, validation errors, month summary, close confirmation, WhatsApp feedback)
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

### 5. WhatsApp Settings
- Toggle to enable/disable daily summary
- "Send Yesterday's Now" button → opens WhatsApp with formatted message of yesterday's expenses
- WorkManager (Dart) handles automatic 8 AM daily trigger in background

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
├── main.py                     # Flet UI (entry point)
├── database.py                 # SQLite CRUD + settings
├── models.py                   # Dataclasses (ExpenseMonth, Expense)
├── flet_template/              # Custom Flutter template for APK build
│   └── {{cookiecutter.out_dir}}/
│       ├── pubspec.yaml        # +workmanager, +share_plus, +sqflite
│       └── lib/
│           ├── main.dart       # WorkManager init + schedule
│           ├── python.dart     # Flet default
│           └── background_task.dart  # Daily WhatsApp summary
├── .github/workflows/
│   └── build-apk.yml           # GitHub Action → APK
├── requirements.txt
├── ARCHITECTURE.md
├── SPEC.md
├── MEMORY.md
├── DECISION.md
└── README.md
```

---

## Key Design Decisions

1. **Month-based periods instead of custom periods** — payment is received at month end, so months are the natural boundary.

2. **Manual "Close Month" instead of automatic** — worker controls when a month is closed (after receiving payment), avoiding confusion.

3. **All expenses this month visible** — worker sees the full monthly picture, not just today's entries.

4. **SQLite over JSON** — structured queries, no loading entire file into memory, built-in aggregations (SUM), ACID compliance.

5. **No login / no cloud** — single user, single device. Simpler and faster.

6. **Flet over KivyMD** — more modern UI, easier deployment, reactive pattern, smaller binary.
