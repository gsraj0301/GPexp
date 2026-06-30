# SPEC - Monthly Expense Tracker

Functional specification and task breakdown for the Monthly Expense Tracker app.

---

## Milestone 1: Project Setup & Database

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 1.1 | Initialize project | Create `expense_tracker/` directory, install Flet (`pip install flet`) | `flet --version` works |
| 1.2 | Create `models.py` | Define `ExpenseMonth` and `Expense` dataclasses | Classes exist with all fields per ARCHITECTURE.md |
| 1.3 | Create `database.py` | Implement `init_db()` — create tables with proper schema | Tables created on first run |
| 1.4 | Create `database.py` | Implement `get_active_month(year, month)` — returns active month or creates one | Returns month record; creates if none exists |
| 1.5 | Create `database.py` | Implement `add_expense(month_id, amount, category, note, date)` | Inserts row, returns expense ID |
| 1.6 | Create `database.py` | Implement `get_expenses(month_id)` — all expenses for a month, ordered by date DESC | Returns list of expenses |
| 1.7 | Create `database.py` | Implement `get_month_total(month_id)` — SUM of all expenses for the month | Returns float |
| 1.8 | Create `database.py` | Implement `close_month(month_id)` — sets `is_closed=1`, `closed_at=now` | Month marked closed |
| 1.9 | Create `database.py` | Implement `create_month(year, month)` — inserts new ExpenseMonth | Returns new month ID |
| 1.10 | Create `database.py` | Implement `get_all_months()` — all months ordered by year DESC, month DESC | Returns list of months with totals |
| 1.11 | Create `database.py` | Implement `get_month(month_id)` — single month by ID | Returns month record |

---

## Milestone 2: Core UI — Main Screen

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 2.1 | Create `main.py` entry point | `main(page)` — initializes DB, gets active month, builds UI | App launches without error |
| 2.2 | AppBar | Show current month name (e.g., "June 2026") and History icon button | Month name is correct, history button visible |
| 2.3 | Expense Input — Amount field | Numeric `TextField` with ₹ prefix, keyboard type = number | Only accepts numbers |
| 2.4 | Expense Input — Category dropdown | `Dropdown` with options: Tea, Water, Biscuit, Snack, Transport, Cartoon, Petrol, Custom | Options visible, one can be selected |
| 2.5 | Expense Input — Custom category | `TextField` appears below dropdown only when "Custom" is selected | Field hidden/shown correctly |
| 2.6 | Expense Input — Date picker | IconButton that opens Flet `DatePicker`, selected date shown | DatePicker opens, date selected |
| 2.7 | Expense Input — Save button | "✓ Save Expense" button — validates inputs → calls `add_expense()` → refreshes list | Expense saved, list updates, form resets |
| 2.8 | Expense List | `ListView` showing all expenses for current month, grouped by date | Expenses appear grouped by day |
| 2.9 | Expense List — Each item | Card/ListTile showing: date, category, note (if exists), amount (₹) | All fields visible and formatted |
| 2.10 | Footer — Month Total | Text showing dynamic total: `"Month Total: ₹0.00"`, updates on add/delete | Total reflects current expenses |
| 2.11 | Footer — Show Total button | OutlinedButton that opens a dialog with the total + expense count | Dialog shows correct info |

---

## Milestone 3: Month Lifecycle

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 3.1 | Close Month button | FilledButton "✅ Close Month" in footer | Button visible |
| 3.2 | Close Month — Confirmation | Dialog: "Close June 2026? This will lock the month and start July 2026." with Cancel/Confirm | Confirmation shows, Cancel dismisses |
| 3.3 | Close Month — Execution | On Confirm: calls `close_month()`, `create_month()` for next month, refreshes screen | Month closed, new month active, list cleared |
| 3.4 | Edge case — Month already exists | If next month's record already exists (e.g., user traveled back in time), just activate it | No duplicate month created |
| 3.5 | First launch | If no months exist, create current month automatically | Month created for current year/month |

---

## Milestone 4: History View

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 4.1 | History — Dialog/Screen | Opens when History icon tapped in AppBar | New view appears |
| 4.2 | History — Month list | List all months (closed + current), each showing: month name, total, status badge | All months listed |
| 4.3 | History — Status badges | Closed months show ✅, current month shows 🔵 (Active) | Badges correct |
| 4.4 | History — Tap month | Tapping a past month expands/shows its expense list | Expenses shown |
| 4.5 | History — Back button | Return to main screen | Main screen shows correct current month |

---

## Milestone 5: Polish & Validation

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 5.1 | Input validation — Amount | Must be > 0, must be a number; None-safe `.value` on mobile | Error snackbar if invalid |
| 5.2 | Input validation — Category | Must be selected (or custom category entered if "Custom" selected) | Error if missing |
| 5.3 | Input validation — Date | Must not be in the future (optional strictness) | Warning if future date |
| 5.4 | Empty state | Show "No expenses yet" message when list is empty | Message visible on fresh month |
| 5.5 | Keyboard type | Amount field uses numeric keyboard on mobile | Appropriate keyboard |
| 5.6 | Cost formatting | All amounts formatted as `₹X,XXX.XX` | Proper Indian/standard formatting |
| 5.7 | Error handling | Database errors show snackbar message | Graceful error handling |

---

## Milestone 6: Packaging & Deployment

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 6.1 | Test as desktop app | Run `flet run main.py` — verify all features work | All milestones 1-5 work |
| 6.2 | Build APK | Use Flet Cloud Build or Colab to generate Android APK | APK file generated |
| 6.3 | Install on Android | Side-load APK on worker's Android phone | App opens, features work |
| 6.4 | Data persistence test | Add expenses, close app, reopen — data still there | SQLite persistence confirmed |

---

## Milestone 7: Daily WhatsApp Expense Summary

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 7.1 | Database helper | Add `get_yesterday_expenses(month_id)` — returns yesterday's expenses for the active month | Returns list of yesterday's expenses with amount, category |
| 7.2 | Custom Flet template | Create `flet_template/` — copy of Flet's default build template | Template can be used with `--template ./flet_template --template-dir build` |
| 7.3 | Flutter deps | Add `workmanager: ^0.9.0`, `share_plus: ^12.0.2`, `sqflite: ^2.3.3` to template `pubspec.yaml` | Dependencies included in generated Flutter project |
| 7.4 | Dart background task | Create `lib/background_task.dart` — WorkManager callback that reads SQLite, formats yesterday's expenses, shares via `SharePlus.instance.share(ShareParams(...))` | Background task code compiles, reads DB, formats message |
| 7.5 | Register WorkManager | Modify `lib/main.dart` to call `Workmanager().initialize()` and schedule daily periodic task at 8:00 AM | Task is registered and scheduled |
| 7.6 | Android permissions | Add `POST_NOTIFICATIONS`, `RECEIVE_BOOT_COMPLETED`, `INTERNET` to `AndroidManifest.xml` | Permissions present in manifest |
| 7.7 | Settings page | Add Settings toggle (enable/disable WhatsApp summary), Test button ("Send yesterday's now") in Python/Flet UI | Settings UI exists, toggle saves preference |
| 7.8 | Config bridge | SharedPreferences bridge: Python writes config, Dart reads it | Config flows from Python ↔ Flutter |
| 7.9 | CI update | Update `build-apk.yml` to use `--template ./flet_template --template-dir build` | Workflow uses custom template |
| 7.10 | Build & verify | Build APK via CI, install on phone, test daily summary | APK builds, WhatsApp intent fires with correct data — Note: `flet_template/` must exclude ios/ dir, set `ios: false` in launcher_icons/native_splash |
| 7.11 | Android mobile fixes | Defensive `(control.value or "").strip()` for None-safe TextField values; try/except around `refresh_expenses()`; AlertDialog instead of snackbar for critical messages | No silent failures on button callbacks |

---

## Milestone 8: Bug Fixes — DatePicker, WhatsApp, Mobile Feedback

| # | Task | Description | Acceptance Criteria |
|---|------|-------------|-------------------|
| 8.1 | Fix DatePicker overlay accumulation | Create single `DatePicker` instance in `main()` scope and reuse it, instead of appending a new one to `page.overlay` on each click | DatePicker works on repeated clicks without "stuck" behavior |
| 8.2 | Fix WhatsApp query scope | Add `get_all_yesterday_expenses()` in `database.py` — queries all months for yesterday's date (not limited to `active_month.id`) | Finds yesterday's expenses regardless of which month they belong to |
| 8.3 | Fix WhatsApp launch feedback | Wrap `send_test_whatsapp` in try/except with AlertDialog for success ("Opening WhatsApp..."), no-expenses, and errors | User always sees what happened when pressing "Send Yesterday's Now" |
| 8.4 | Replace snackbars with AlertDialogs | Replace all snackbars in `save_expense()` (success, amount error, category error, future date, DB error) and `refresh_expenses()` with AlertDialogs | All user feedback visible on mobile (snackbars invisible on Android) |
| 8.5 | Fix DatePicker timezone offset bug | In `set_date()`, handle timezone-aware datetimes from DatePicker — convert to local time via `astimezone()` before extracting `.date()` | Selecting June 29 in DatePicker shows "Jun 29" in the app, not "Jun 28" |
| 8.6 | Fix WhatsApp launch on Android | Replace `whatsapp://send?text=` with `https://wa.me/?text=` which works more reliably on Android via `url_launcher`. Add immediate debug alert showing expense count. Add clipboard fallback if URL launch fails. | Pressing "Send Yesterday's Now" opens WhatsApp with preloaded message on installed APK |

---

## Data Flow Summary

```
User Input (amount, category, date)
       │
       ▼
main.py validates input
       │
       ▼
database.add_expense(month_id, amount, category, note, date)
       │
       ▼
SQLite INSERT INTO expenses (...)
       │
       ▼
main.py refreshes:
  - Expense List (get_expenses)
  - Month Total (get_month_total)
       │
       ▼
UI updates with new data
```

## State Management

- All state is driven from SQLite — no in-memory duplication
- Active month ID is fetched from DB each time (single source of truth)
- UI refreshes by re-querying DB after each mutation (add, close month)
- This approach is simple, consistent, and avoids sync bugs
