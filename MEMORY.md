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
- `settings`: key (PK), value — key-value config store (whatsapp_enabled, whatsapp_last_sent)
- UNIQUE(year, month) constraint on ExpenseMonth
- `DB_PATH` now uses `FLET_APP_STORAGE_DATA` env var (set by Flutter → getApplicationDocumentsDirectory)

## Key Design Decisions
| Decision | Chosen | Why |
|----------|--------|-----|
| Platform | Flet desktop + Android | Desktop dev, mobile deploy, Python (familiar) |
| Periods | Monthly | Worker gets paid at month end |
| Month change | Auto-detect | On July 1st, auto-close June, start July fresh |
| Close Month | Manual button | Worker controls when payment is received |
| Categories | Dropdown (Tea/Water/Biscuit/Snack/Transport/Cartoon/Petrol) + custom text field | Both options always visible |
| Date picker | Yes, with calendar widget | Worker requested date selection |
| Note field | Removed by user request | Was added, then removed |
| Storage | SQLite | Simple, ACID, no server |
| Build | GitHub Actions | 8GB RAM laptop too slow for local Android build |
| WhatsApp | Android Share Intent (semi-auto) | Worker opens app daily, toggle ON, WorkManager fires at 8AM, opens share sheet for WhatsApp |
| Template | Custom cookiecutter template in repo (`flet_template/`) | Needed to inject WorkManager + share_plus + sqflite Flutter dependencies and Dart code |

## Features Implemented
- [x] Add expense (amount + category/custom + date)
- [x] Expense list grouped by date
- [x] Month total (text + button with dialog)
- [x] Close Month (with confirmation dialog)
- [x] Auto-detect month change (closes previous, creates current)
- [x] History view (all months with totals, tap to see details)
- [x] Input validation (amount > 0, future date warning)
- [x] Error handling (DB errors caught with snackbar/dialog)
- [x] None-safe `.value` handling for mobile (`(control.value or "").strip()` pattern)
- [x] `refresh_expenses()` wrapped in try/except to prevent UI freeze
- [x] Build pipeline (GitHub Actions → APK)
- [x] WhatsApp daily summary (toggle in Settings, WorkManager background task at 8AM, share_plus intent)
- [x] Custom Flutter template (flet_template/ with WorkManager + share_plus + sqflite)
- [x] DatePicker single instance (fixed overlay accumulation bug — date picker no longer "stuck")
- [x] All feedback uses AlertDialog (snackbars invisible on mobile — replaced everywhere)
- [x] WhatsApp "Send Yesterday" queries all months (not just active month, finds expenses across month boundaries)

## Files
```
expense_tracker/
├── main.py                     # Flet UI (entry point)
├── models.py                   # Dataclasses (ExpenseMonth, Expense)
├── database.py                 # SQLite CRUD + settings + get_yesterday_expenses + get_all_yesterday_expenses
├── requirements.txt            # flet (for GitHub Actions build)
├── pyproject.toml              # (optional) project config
├── .gitignore
├── .github/workflows/
│   └── build-apk.yml           # GitHub Action → Android APK
├── flet_template/              # Custom cookiecutter Flutter template
│   ├── cookiecutter.json
│   ├── cookiecutter_extensions.py
│   └── {{cookiecutter.out_dir}}/
│       ├── pubspec.yaml        # deps: workmanager, share_plus, sqflite
│       ├── lib/
│       │   ├── main.dart       # Modified: registers WorkManager, schedules daily 8AM task
│       │   ├── python.dart     # (unchanged from default)
│       │   └── background_task.dart  # NEW: daily SQLite query + WhatsApp share
│       └── android/            # Android platform files (stripped non-Android dirs)
├── ARCHITECTURE.md
├── SPEC.md
└── MEMORY.md                   # This file
```

## Flet Version-Specific Gotchas
- `page.open()` → does NOT exist. Use `page.dialog = dlg; dlg.open = True; page.update()`
- `ft.alignment.center` → does NOT exist as attribute. Use `ft.alignment.center` not on `flet.controls.alignment`
- `TextField(prefix_text=...)` → NOT supported. Use `label="Amount (₹)"` instead
- `DatePicker` → use `page.overlay.append(dp); dp.open = True; page.update()` (not `page.open(dp)`)
- Custom template: `--template ./flet_template` — template dir must have `cookiecutter.json` at root
- Template omits non-Android platforms (ios/, linux/, macos/, windows/, web/) — safe for APK-only builds
- WorkManager: `callbackDispatcher` must be top-level with `@pragma('vm:entry-point')`
- `share_plus` v12.0.2: `SharePlus.instance.share(ShareParams(text:, subject:))` — v7 API `Share.share()` removed
- `sqflite` + Python's `sqlite3` access the same `.db` file — SQLite handles concurrent access via locking
- `FLET_APP_STORAGE_DATA` = `getApplicationDocumentsDirectory().path` (set by Flutter, available in Python)
- `TextField.value` can be `None` on Android → always use `(control.value or "").strip()` pattern
- `refresh_expenses()` must be wrapped in try/except — any exception there freezes the save button silently
- Snackbars can be invisible on mobile (overlapped by nav bars) → always use AlertDialog for ALL user feedback (not just important messages)
- DatePicker: create ONE instance and append to `page.overlay` once; reuse it each time. Never create a new DatePicker on each click — multiple overlays break the picker
- AlertDialog helper pattern: define a reusable `show_alert(title, message)` that creates a dialog, assigns to `page.dialog`, opens it, and calls `page.update()`. Avoid inline `page.snack_bar` entirely for mobile targets

## GitHub Actions
- Workflow: `.github/workflows/build-apk.yml`
- Trigger: push to `main` OR manual `workflow_dispatch`
- APK output: `build/apk/` → uploaded as artifact `expense-tracker-apk`
- Build command: `flet build apk --project expense_tracker --product "Expense Tracker" --org com.expensetracker --template ./flet_template --yes`
- Simplified workflow (removed setup-java, setup-android — Flet handles these)

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
flet build apk --project expense_tracker --product "Expense Tracker" --org com.expensetracker --template ./flet_template --yes
```

## WhatsApp Daily Summary — How It Works
1. **Python/Flet UI:** Settings page with toggle → writes `whatsapp_enabled` to SQLite `settings` table
2. **Custom Flutter template** (`flet_template/`): injects `workmanager`, `share_plus`, `sqflite` into Flutter project
3. **App start** (Flutter `main.dart`): calls `Workmanager().initialize(callbackDispatcher)`, schedules periodic task every 24h with initial delay to next 8:00 AM
4. **Background task** (`background_task.dart`):
   - Opens SQLite at `{getApplicationDocumentsDirectory()}/expenses.db`
   - Checks `whatsapp_enabled` → skips if false
   - Checks `whatsapp_last_sent` → skips if already today
   - Queries yesterday's expenses for active month
   - Formats: `📅 Yesterday's Expenses (Jun 28)\n\nTea\n  • ₹50.00\n...\n─────────────\nTotal: ₹150.00`
   - Calls `SharePlus.instance.share(ShareParams(text:, subject:))` → Android system share sheet → user taps WhatsApp
   - Writes `whatsapp_last_sent = YYYY-MM-DD`
5. **Test button:** "Send Yesterday's Now" in Settings — same formatting, uses `page.launch_url(f"whatsapp://send?text={encoded}")` for direct WhatsApp open (shows AlertDialog if no yesterday expenses)

## Build Fix History
### Session 1 — WHatsApp Feature + Build Debugging
- **Issue:** Flet 0.85.3 requires `share_plus ^12.0.1` but template had `^7.2.2`
- **Fix:** Bumped to `^12.0.2`, updated Dart API from `Share.share()` → `SharePlus.instance.share(ShareParams(...))`
- **Issue:** `flutter_launcher_icons` missing from pubspec → Flet CLI `KeyError`
- **Fix:** Restored dev_deps with `flutter_launcher_icons: ^0.14.1` but set `ios: false` (template strips ios/ dir)
- **Issue:** `workmanager ^0.5.2` uses deprecated Flutter v1 embedding APIs (Registrar, PluginRegistrantCallback)
- **Fix:** Bumped to `^0.9.0`, updated API: `NetworkType.not_required` → `NetworkType.notRequired`, `ExistingWorkPolicy` → `ExistingPeriodicWorkPolicy`
- **Issue:** Button callbacks silently fail on Android — `TextField.value` can be `None`, `refresh_expenses()` exceptions freeze UI
- **Fix:** Defensive `(control.value or "").strip()` pattern, try/except around `refresh_expenses()`, AlertDialog instead of snackbar for WhatsApp empty state

### Session 2 — DatePicker Overlay Bug + WhatsApp Cross-Month + AlertDialog Everywhere
- **Issue:** DatePicker gets "stuck" after repeated taps — multiple `DatePicker` instances accumulate in `page.overlay`, breaking the picker
- **Fix:** Create ONE `DatePicker` instance at component scope, append to `page.overlay` once, reuse in `pick_date()`
- **Issue:** WhatsApp "Send Yesterday's Now" doesn't find expenses — queries by `active_month.id` but yesterday's expenses may be in a different (closed) month
- **Fix:** Added `get_all_yesterday_expenses()` in `database.py` — queries ALL months for yesterday's date via `WHERE date = ?` without month filter
- **Issue:** WhatsApp button shows no feedback on mobile — if `get_yesterday_expenses` returns empty, the AlertDialog may be invisible; no error on launch failure
- **Fix:** Wrapped entire `send_test_whatsapp` in try/except with AlertDialog for "Opening WhatsApp...", no-expenses, and error cases
- **Issue:** All snackbar feedback invisible on mobile — success, error, and validation messages hidden behind nav bars
- **Fix:** Replaced ALL `page.snack_bar` calls with `show_alert(title, message)` helper (AlertDialog). Covers save_expense (success + all validation errors), refresh_expenses, confirm_close_month, and auto-close month change

## Next Steps (Current)
1. Install latest APK from GitHub Actions (triggered on push) on phone
2. Test: add expense for a past date — should save with visible AlertDialog confirmation
3. Test: tap "Send Yesterday's Now" in Settings — should open WhatsApp with yesterday's expenses (now queries ALL months, not just active month)
4. Verify WorkManager fires at 8:00 AM (or change phone time to test)
5. If save still fails, check adb logcat for Python/Dart exceptions

## Future Ideas
- Category presets configurable in Settings
- Export to CSV/PDF
- Edit/delete existing expense
- Backup DB to Google Drive
