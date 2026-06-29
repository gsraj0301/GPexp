# DECISION.md — Lessons Learned

Every decision, problem, and fix encountered while building the Monthly Expense Tracker app. Use this as a checklist/guide for the next project.

---

## 1. Framework & Architecture

### 1.1 Chose Flet (Python → Flutter) over KivyMD / Tkinter

**Why:** Reactive UI, Python for logic, desktop dev → mobile APK deploy, no Android Studio needed.

**Trade-off:** Flet is relatively young. Version-specific bugs are common. Pin the exact version (`flet: 0.85.3` in pubspec) and test thoroughly before upgrading.

### 1.2 SQLite over JSON / Cloud

**Why:** Single user, single device. Zero setup, ACID, no network dependency.

**Trade-off:** On Android, the database file lives in the app's private directory (`getApplicationDocumentsDirectory()`). The path is passed to Python via the `FLET_APP_STORAGE_DATA` environment variable, which Flutter's Dart code sets before starting the Python runtime.

### 1.3 Monthly Periods over Custom Ranges

**Why:** Worker gets paid at month end — months are the natural boundary.

**Design:** Manual "Close Month" button (worker controls the cutoff) + auto-detect month change on app start (if a new month has started, auto-close the previous one).

### 1.4 Categories

**Current choices:** Tea, Water, Biscuit, Snack, Transport, Cartoon, Petrol + custom text field.

**Lesson:** Dropdown options are app-specific and will change per user. Make them configurable from the start if building for multiple users.

---

## 2. Data Layer

### 2.1 Database Path on Android (Critical)

```python
DB_PATH = os.environ.get("FLET_APP_STORAGE_DATA", ".")
if os.path.isdir(DB_PATH):
    DB_PATH = os.path.join(DB_PATH, "expenses.db")
```

- On desktop: `FLET_APP_STORAGE_DATA` is not set → falls back to `.` → uses `./expenses.db`
- On Android: Flutter sets it to `getApplicationDocumentsDirectory().path` → `/data/.../app_flutter/expenses.db`

**Gotcha:** The env var is set in Dart (`environmentVariables.putIfAbsent("FLET_APP_STORAGE_DATA", () => appDataPath)`) and passed to SeriousPython. If SeriousPython doesn't propagate env vars correctly, the DB path breaks. Test on device early.

### 2.2 SQLite Concurrent Access

Both Python's `sqlite3` (main app) and Dart's `sqflite` (WorkManager background task) access the same `.db` file. SQLite handles this via file-level locking. In practice, it works fine — the background task runs at 8 AM while the user is unlikely to be actively using the app.

**Lesson:** Test concurrent access scenarios. If both access the DB simultaneously, the background task could block the UI.

---

## 3. WhatsApp Daily Summary Feature

### 3.1 Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Python toggle | Flet Switch | Enable/disable in Settings |
| Scheduler | WorkManager (Dart) | Daily task at 8 AM |
| DB reader | sqflite (Dart) | Read yesterday's expenses |
| Share | share_plus (Dart) | Open Android share sheet |

### 3.2 Why WorkManager (not Python background)

Flet/SeriousPython runs Python in the foreground. When the app is closed, Python stops. Background execution requires native Android APIs. WorkManager wraps Android's WorkManager API and can execute Dart code even when the app is killed.

### 3.3 Why Custom Flutter Template

Flet 0.85.3's default Flutter template does NOT include `workmanager`, `share_plus`, or `sqflite`. To add these dependencies, you must create a custom cookiecutter template that extends the default one.

**Template structure:**
```
flet_template/
├── cookiecutter.json              # Template variables
├── cookiecutter_extensions.py     # Jinja2 extensions
└── {{cookiecutter.out_dir}}/      # Template files
    ├── pubspec.yaml               # +workmanager, +share_plus, +sqflite
    ├── lib/
    │   ├── main.dart              # +WorkManager init, +schedule task
    │   ├── python.dart            # Unchanged from default
    │   └── background_task.dart   # New: daily summary logic
    └── android/                   # Only Android (other platforms stripped)
```

**Build command:**
```bash
flet build apk --template ./flet_template --yes
```

---

## 4. Build Debugging — Every Error We Hit

### Error 1: `share_plus` version conflict

**Symptom:**
```
Because flet >=0.80.0 depends on share_plus ^12.0.1
and expense_tracker depends on share_plus ^7.2.2, version solving failed.
```

**Root cause:** Flet 0.85.3 transitively requires `share_plus ^12.0.1`. Our template pinned `^7.2.2`.

**Fix:** Bumped to `share_plus: ^12.0.2`.

**Dart API change (v7 → v12):**
```dart
// OLD (v7)
await Share.share(text, subject: "Daily Expenses");

// NEW (v12)
await SharePlus.instance.share(
  ShareParams(text: text, subject: "Daily Expenses"),
);
```

**Lesson for next app:** When pinning a Flet version, check its transitive dependency requirements. Run `flet build` on a minimal template FIRST before adding custom deps.

### Error 2: `flutter_launcher_icons` missing

**Symptom:**
```
KeyError: 'flutter_launcher_icons'
at hash.update(pubspec["flutter_launcher_icons"])
```

**Root cause:** Flet's `customize_icons()` method reads `pubspec["flutter_launcher_icons"]` directly. We removed it entirely thinking it wasn't needed.

**Fix:** Restored `flutter_launcher_icons` and `flutter_native_splash` with `ios: false`.

**Lesson for next app:** Don't remove dev_dependencies from Flet's template unless you're certain the build process doesn't reference them. Flet's CLI has hardcoded lookups for these keys.

### Error 3: `workmanager` 0.5.2 incompatible with Flutter 3.x

**Symptom:**
```
Unresolved reference 'shim'
Unresolved reference 'registerWith'
Unresolved reference 'PluginRegistrantCallback'
```

**Root cause:** `workmanager ^0.5.2` uses Flutter v1 embedding APIs (`Registrar`, `PluginRegistrantCallback`, `shim`) that were removed in Flutter 3.x. Flet 0.85.3 uses Flutter 3.41.7.

**Fix:** Bumped to `workmanager: ^0.9.0`.

**API changes (0.5.x → 0.9.x):**
```dart
// OLD
constraints: Constraints(networkType: NetworkType.not_required),
existingWorkPolicy: ExistingWorkPolicy.replace,
Workmanager().initialize(callbackDispatcher, isInDebugMode: false);

// NEW
constraints: Constraints(networkType: NetworkType.notRequired),  // camelCase
existingWorkPolicy: ExistingPeriodicWorkPolicy.replace,          // renamed type
Workmanager().initialize(callbackDispatcher);                    // isInDebugMode deprecated
```

**Lesson for next app:** Always check if a Flutter plugin uses v1 vs v2 embedding. Packages published before 2022 likely use v1 APIs and won't work with Flutter 3.x+.

### Error 4: `flutter_launcher_icons` iOS path crash

**Symptom:**
```
PathNotFoundException: Cannot open file, path = 'ios/Runner/...'
```

**Root cause:** Our template strips non-Android platform directories (`ios/`, `linux/`, etc.). `flutter_launcher_icons` with `ios: true` tries to write iOS icon files to the missing `ios/` directory.

**Fix:** Set `ios: false` in both `flutter_launcher_icons` and `flutter_native_splash` config.

**Lesson for next app:** If you strip platforms from a template, also disable their icon/splash generation.

---

## 5. Mobile-Specific Runtime Fixes

### 5.1 `TextField.value` Can Be `None` on Android

**Symptom:** Button callbacks silently fail — no snackbar, no error, just nothing happens.

**Root cause:** `amount_field.value.strip()` throws `AttributeError` when `.value` is `None`. On desktop, Flet defaults `TextField.value` to `""`. On Android, it can be `None`.

**Fix — Always use this pattern:**
```python
amount_str = (amount_field.value or "").strip()
typed_category = (custom_category_field.value or "").strip()
```

**Lesson for next app:** NEVER call `.strip()` directly on a control's `.value`. Always default to empty string first. This applies to ALL Flet projects targeting mobile.

### 5.2 `refresh_expenses()` Can Freeze the UI

**Symptom:** Save button looks stuck — no visual response, but app isn't crashed.

**Root cause:** `refresh_expenses()` was not wrapped in try/except. If `get_expenses()` or `get_month_total()` throws (e.g., DB locked, corrupted), the exception propagates up and the UI hangs silently.

**Fix:**
```python
def refresh_expenses():
    try:
        # ... all the list building logic ...
    except Exception as ex:
        page.snack_bar = ft.SnackBar(ft.Text(f"Error refreshing: {str(ex)}"), open=True)
    page.update()
```

**Lesson for next app:** Any function called from a button callback that touches the database should have error handling. A silent exception in `refresh_expenses()` means "save completes but UI never updates" — the user thinks it's broken.

### 5.3 Snackbars Can Be Invisible on Mobile

**Symptom:** Error messages appear briefly or are hidden behind navigation bars.

**Fix:** Use `AlertDialog` for critical feedback instead of snackbar:
```python
dlg = ft.AlertDialog(title=ft.Text("No Expenses"), content=ft.Text("..."),
    actions=[ft.TextButton("OK", on_click=lambda e: close_dialog(dlg))])
page.dialog = dlg
dlg.open = True
page.update()
```

**Lesson for next app:** Snackbars are unreliable on mobile. Use dialogs for anything the user MUST see.

### 5.4 Always Call `page.update()` Before Expensive Operations

```python
page.snack_bar = ft.SnackBar(ft.Text("Expense saved ✅"), open=True)
page.update()          # <-- Render the snackbar NOW
refresh_expenses()     # <-- Then do the refresh (might fail)
```

If `refresh_expenses()` throws, the user still sees the success snackbar. Without the extra `page.update()`, a failure in `refresh()` silently erases the success feedback.

---

## 6. Build Pipeline

### 6.1 GitHub Actions Workflow

`.github/workflows/build-apk.yml` triggers on push to `main` or manual `workflow_dispatch`.

```yaml
- run: pip install flet
- run: flet build apk --project expense_tracker --product "Expense Tracker" \
        --org com.expensetracker --template ./flet_template --yes
- uses: actions/upload-artifact@v4
  with:
    name: expense-tracker-apk
    path: build/apk/
```

**Lesson:** Don't install `setup-java` or `setup-android` — Flet's CLI handles Android SDK setup. The GitHub Actions Ubuntu runner already has everything needed.

### 6.2 Flet Build Timing

- First build: ~6-8 minutes (downloads Flutter, Android SDK, NDK, builds)
- Subsequent builds: ~3-5 minutes (cached dependencies)
- Flet installs Flutter, JDK, Android SDK, and NDK automatically

### 6.3 APK Output

The APK ends up at `build/apk/` relative to the project root. It's unsigned (debug signing). For production, add a signing config, but for personal use, debug-signed is fine.

---

## 7. Checklist for the Next App

### Before writing code
- [ ] Pick a stable Flet version and check its transitive Flutter dependencies
- [ ] If custom Flutter deps are needed, plan the custom template from day 1
- [ ] Test a minimal `flet build apk` on CI before adding custom code

### During development
- [ ] Test ALL button callbacks on actual Android device (not just desktop)
- [ ] Always use `(control.value or "")` pattern for TextField reads
- [ ] Wrap all DB-facing refresh functions in try/except
- [ ] Use AlertDialog for critical errors, not snackbar
- [ ] Call `page.update()` before expensive operations

### Before build
- [ ] Update pubspec.yaml versions to match Flet's transitive requirements
- [ ] Set `ios: false` in launcher_icons/native_splash if ios/ dir is stripped
- [ ] Check all CI logs for dependency conflicts, not just compilation errors
- [ ] Keep MEMORY.md + DECISION.md up to date as you discover issues

### Version pinning reference
| Package | Version | Rationale |
|---------|---------|-----------|
| `flet` | 0.85.3 | Stable, works with Flutter 3.41.7 |
| `share_plus` | ^12.0.2 | Required by Flet, v7 API removed |
| `workmanager` | ^0.9.0 | v0.5.x uses deprecated v1 embedding |
| `sqflite` | ^2.3.3 | Latest stable |
| `flutter_launcher_icons` | ^0.14.1 | Flet CLI reads this key |
| `flutter_native_splash` | ^2.4.1 | Keep for safety |
