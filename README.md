# Monthly Expense Tracker

A lightweight mobile/desktop app for tracking daily expenses on a monthly basis. Built with **Flet (Python + Flutter)**, using **SQLite** for local storage. No server, no login.

## Features

- Add expenses with amount, category, date
- Expense list grouped by date
- Month total with summary dialog
- Close month (lock period, start next)
- History view (all months, tap to expand)
- Auto-detect month change on app start
- **WhatsApp daily summary** — toggle in Settings, background task at 8 AM via WorkManager, or tap "Send Yesterday's Now" to share instantly
- **Custom categories** — pick from dropdown (Tea, Water, Biscuit, Snack, Transport, Cartoon, Petrol) or type your own

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| UI Framework | Flet 0.85.3 |
| Storage | SQLite (single `expenses.db`) |
| Android Build | GitHub Actions → APK |
| Background Tasks | WorkManager (Dart) |
| Share Intent | share_plus (Dart) |

## Screenshots

| Main Screen | History | WhatsApp Settings |
|-------------|---------|------------------|
| Add expenses, view list, month total | Browse all months, tap to see details | Toggle daily summary, send now |

## Quick Start (Desktop)

```bash
python -m venv .venv
source .venv/bin/activate
pip install flet
python main.py
```

## Build APK

```bash
pip install flet
flet build apk \
  --project expense_tracker \
  --product "Expense Tracker" \
  --org com.expensetracker \
  --template ./flet_template \
  --yes
```

GitHub Actions builds automatically on push to `main`.

## Project Structure

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
│   └── build-apk.yml           # Build & upload APK
├── requirements.txt
├── ARCHITECTURE.md
├── SPEC.md
├── MEMORY.md
├── DECISION.md
└── README.md
```

## How WhatsApp Summary Works

1. **Enable** the toggle in Settings → Python writes `whatsapp_enabled` to SQLite
2. **Automatic** — WorkManager fires daily at 8:00 AM (via Flutter/Dart), reads yesterday's expenses, opens share sheet
3. **Manual** — tap "Send Yesterday's Now" in Settings → opens WhatsApp with formatted message instantly

> **Important:** The manual button's handler must be `async def` because `page.launch_url()` in Flet 0.85.3 is an async method. Calling it from a sync function without `await` silently discards the coroutine — the URL never launches and no error is shown.

Format:
```
📅 Yesterday's Expenses (Jun 29)

Tea
  • ₹30.00
  • ₹20.00

Biscuit
  • ₹15.00

─────────────
Total: ₹65.00
```

## Data Model

```
ExpenseMonth              Expense
│ id (PK) ◄──────────────│ month_id (FK)
│ year                    │ amount
│ month                   │ category
│ is_closed               │ date
│ closed_at               │ note
│ created_at              │
```

## Gotchas

- **Async Flet APIs:** Many Flet APIs (e.g., `page.launch_url()`) are `async def` but are not documented as such. If a button callback calls an async function, the callback itself must be `async def` with `await` on the call. Calling an `async def` without `await` returns an unexecuted coroutine — no error, no action.
- **`TextField.value` may be `None`:** On Android, always use `(control.value or "").strip()` instead of `control.value.strip()`.
- **Snackbars invisible on mobile:** Use `AlertDialog` for important user feedback.
- **DatePicker returns UTC:** Flutter serializes local midnight to UTC. Use `d.astimezone().date()` to convert back to local time.
- **DatePicker overlay accumulation:** Create one `DatePicker` instance and reuse it. Appending a new one on each click breaks the picker after repeated opens.
- **Database path:** On Android, the DB lives in `getApplicationDocumentsDirectory()`, passed via `FLET_APP_STORAGE_DATA` env var. On desktop, it falls back to the current directory.
