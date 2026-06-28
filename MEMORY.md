# Memory — Monthly Expense Tracker

## Project Overview
Monthly expense tracker for a single worker built with **Flet (Python + Flutter)**. Local SQLite storage, no login, no cloud.

## Tech Stack
- **Language:** Python 3.12
- **Framework:** Flet 0.85.3
- **Storage:** SQLite (`expenses.db`, auto-created)
- **Build:** GitHub Actions → APK artifact

## Data Model
- `ExpenseMonth`: id, year, month, is_closed, closed_at, created_at
- `Expense`: id, month_id (FK), amount, category, note, date
- UNIQUE(year, month) constraint on ExpenseMonth

## Key Design Decisions
| Decision | Chosen | Why |
|----------|--------|-----|
| Platform | Flet desktop + Android | Desktop dev, mobile deploy, Python (familiar) |
| Periods | Monthly | Worker gets paid at month end |
| Month change | Auto-detect | On July 1st, auto-close June, start July fresh |
| Close Month | Manual button | Worker controls when payment is received |
| Categories | Dropdown (Food/Transport/Materials/Other) + custom text field | Both options always visible |
| Date picker | Yes, with calendar widget | Worker requested date selection |
| Note field | Removed by user request | Was added, then removed |
| Storage | SQLite | Simple, ACID, no server |
| Build | GitHub Actions | 8GB RAM laptop too slow for local Android build |

## Features Implemented
- [x] Add expense (amount + category/custom + date)
- [x] Expense list grouped by date
- [x] Month total (text + button with dialog)
- [x] Close Month (with confirmation dialog)
- [x] Auto-detect month change (closes previous, creates current)
- [x] History view (all months with totals, tap to see details)
- [x] Input validation (amount > 0, future date warning)
- [x] Error handling (DB errors caught with snackbar)
- [x] Build pipeline (GitHub Actions → APK)

## Files
```
expense_tracker/
├── main.py                 # Flet UI (entry point)
├── models.py               # Dataclasses (ExpenseMonth, Expense)
├── database.py             # SQLite CRUD operations
├── requirements.txt        # flet (for GitHub Actions build)
├── .gitignore
├── .github/workflows/
│   └── build-apk.yml       # GitHub Action → Android APK
├── ARCHITECTURE.md
├── SPEC.md
└── MEMORY.md               # This file
```

## Flet Version-Specific Gotchas
- `page.open()` → does NOT exist. Use `page.dialog = dlg; dlg.open = True; page.update()`
- `ft.alignment.center` → does NOT exist as attribute. Use `ft.alignment.center` not on `flet.controls.alignment`
- `TextField(prefix_text=...)` → NOT supported. Use `label="Amount (₹)"` instead
- `DatePicker` → use `page.overlay.append(dp); dp.open = True; page.update()` (not `page.open(dp)`)

## GitHub Actions
- Workflow: `.github/workflows/build-apk.yml`
- Trigger: push to `main` OR manual `workflow_dispatch`
- APK output: `build/apk/` → uploaded as artifact `expense-tracker-apk`

## To Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install flet
python main.py
```

## To Build APK (on a powerful machine or CI)
```bash
pip install flet
flet build apk --project expense_tracker --product "Expense Tracker" --org com.expensetracker
```
