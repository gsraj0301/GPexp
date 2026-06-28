import flet as ft
from datetime import datetime, date

from database import (
    init_db, get_active_month, get_all_months, get_month,
    add_expense, get_expenses, get_month_total,
    close_month, create_month,
)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def main(page: ft.Page):
    page.title = "Expense Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    init_db()

    now = datetime.now()
    active_month = get_active_month(now.year, now.month)

    def get_month_label(year: int, month: int) -> str:
        return f"{MONTH_NAMES[month]} {year}"

    if active_month.year < now.year or (active_month.year == now.year and active_month.month < now.month):
        closed_label = get_month_label(active_month.year, active_month.month)
        closed_total = get_month_total(active_month.id)
        close_month(active_month.id)
        active_month = create_month(now.year, now.month)
        page.snack_bar = ft.SnackBar(
            ft.Text(
                f"{closed_label} closed (₹{closed_total:,.2f}). Now tracking {get_month_label(active_month.year, active_month.month)}."
            ),
            open=True,
        )

    def refresh_expenses():
        nonlocal active_month
        expenses = get_expenses(active_month.id)
        total = get_month_total(active_month.id)

        total_text.value = f"Month Total: ₹{total:,.2f}"

        controls = []
        current_date = None
        for exp in expenses:
            exp_date = exp.date.strftime("%Y-%m-%d")
            if exp_date != current_date:
                current_date = exp_date
                controls.append(
                    ft.Text(exp.date.strftime("%b %d, %Y"), size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_600)
                )
            controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.BLUE_400),
                    title=ft.Text(exp.category, size=15),
                    subtitle=ft.Text(exp.note, size=12, color=ft.Colors.GREY_600) if exp.note else None,
                    trailing=ft.Text(f"₹{exp.amount:,.2f}", size=15, weight=ft.FontWeight.W_600),
                    dense=True,
                )
            )

        if not controls:
            controls.append(
                ft.Container(
                    content=ft.Text("No expenses yet", color=ft.Colors.GREY, italic=True),
                    padding=20,
                )
            )

        expense_list.controls = controls
        page.update()

    # --- Expense Input Form ---

    amount_field = ft.TextField(
        label="Amount (₹)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=140,
        dense=True,
    )

    category_dropdown = ft.Dropdown(
        label="Pick a category",
        options=[
            ft.dropdown.Option("Food"),
            ft.dropdown.Option("Transport"),
            ft.dropdown.Option("Materials"),
            ft.dropdown.Option("Other"),
        ],
        width=180,
        dense=True,
    )

    custom_category_field = ft.TextField(
        label="Or type your own category",
        hint_text="e.g. Tea, Medicine, ...",
        dense=True,
    )

    selected_date = date.today()

    date_text = ft.Text(selected_date.strftime("%b %d, %Y"), size=14)

    def pick_date(e):
        dp = ft.DatePicker(
            on_change=lambda e: set_date(e.control.value),
        )
        page.overlay.append(dp)
        dp.open = True
        page.update()

    def set_date(d: date):
        nonlocal selected_date
        selected_date = d
        date_text.value = selected_date.strftime("%b %d, %Y")
        page.update()

    date_button = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, tooltip="Pick date", on_click=pick_date)

    def save_expense(e):
        nonlocal selected_date
        amount_str = amount_field.value.strip()
        picked_category = category_dropdown.value
        typed_category = custom_category_field.value.strip()

        if not amount_str:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter an amount"), open=True)
            page.update()
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Amount must be a positive number"), open=True)
            page.update()
            return

        category = picked_category or typed_category
        if not category:
            page.snack_bar = ft.SnackBar(ft.Text("Pick a category or type your own"), open=True)
            page.update()
            return

        if selected_date > date.today():
            page.snack_bar = ft.SnackBar(ft.Text("Date cannot be in the future"), open=True)
            page.update()
            return

        exp_date = selected_date.isoformat()

        try:
            add_expense(active_month.id, amount, category, "", exp_date)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error saving: {str(ex)}"), open=True)
            page.update()
            return

        amount_field.value = ""
        category_dropdown.value = None
        custom_category_field.value = ""
        selected_date = date.today()
        date_text.value = selected_date.strftime("%b %d, %Y")

        page.snack_bar = ft.SnackBar(ft.Text("Expense saved ✅"), open=True)
        refresh_expenses()

    save_button = ft.FilledButton(
        content=ft.Row([ft.Icon(ft.Icons.CHECK), ft.Text("Save")], tight=True),
        on_click=save_expense,
    )

    input_form = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([amount_field, category_dropdown], spacing=10),
                custom_category_field,
                ft.Row([date_button, date_text, ft.Container(expand=True), save_button], spacing=5),
            ], spacing=8),
            padding=12,
        )
    )

    # --- Expense List ---

    total_text = ft.Text("Month Total: ₹0.00", size=16, weight=ft.FontWeight.BOLD)

    expense_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)

    # --- Footer Buttons ---

    def show_total_dialog(e):
        total = get_month_total(active_month.id)
        expenses = get_expenses(active_month.id)
        count = len(expenses)

        dlg = ft.AlertDialog(
            title=ft.Text("Month Summary"),
            content=ft.Column([
                ft.Text(f"Total Expenses: ₹{total:,.2f}", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Number of items: {count}", size=16),
            ], tight=True, spacing=8),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dialog(dlg))],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def close_dialog(dlg):
        dlg.open = False
        page.update()

    show_total_btn = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED), ft.Text("Show Total")], tight=True),
        on_click=show_total_dialog,
    )

    def close_month_click(e):
        total = get_month_total(active_month.id)
        label = get_month_label(active_month.year, active_month.month)
        dlg = ft.AlertDialog(
            title=ft.Text(f"Close {label}?"),
            content=ft.Column([
                ft.Text(f"This will lock {label} and start the next month.", size=14),
                ft.Text(f"Current total: ₹{total:,.2f}", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Make sure you've received the payment.", size=12, color=ft.Colors.GREY_600),
            ], tight=True, spacing=8),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dlg)),
                ft.FilledButton("Confirm Close", on_click=lambda e: confirm_close_month(dlg)),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def confirm_close_month(dlg):
        nonlocal active_month
        close_dialog(dlg)
        total = get_month_total(active_month.id)

        close_month(active_month.id)

        next_year = active_month.year + (active_month.month // 12)
        next_month = (active_month.month % 12) + 1
        active_month = create_month(next_year, next_month)

        page.appbar.title = ft.Text(get_month_label(active_month.year, active_month.month), size=22, weight=ft.FontWeight.BOLD)
        page.snack_bar = ft.SnackBar(ft.Text(f"{get_month_label(active_month.year, active_month.month)} started! Total paid: ₹{total:,.2f}"), open=True)
        refresh_expenses()

    close_month_btn = ft.FilledButton(
        content=ft.Row([ft.Icon(ft.Icons.LOCK_CLOCK_OUTLINED), ft.Text("Close Month")], tight=True),
        on_click=close_month_click,
    )

    footer_row = ft.Row([show_total_btn, close_month_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # --- History View ---

    history_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

    def build_history():
        months = get_all_months()
        controls = []
        for m, total in months:
            label = get_month_label(m.year, m.month)
            status = "✅" if m.is_closed else "🔵 Active"
            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.ListTile(
                            title=ft.Text(f"{label}  {status}", size=15),
                            subtitle=ft.Text(f"Total: ₹{total:,.2f}", size=13, color=ft.Colors.GREY_600),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                            on_click=lambda _, month_id=m.id: show_month_detail(month_id),
                        ),
                        padding=4,
                    )
                )
            )

        if not controls:
            controls.append(
                ft.Container(
                    content=ft.Text("No history yet", color=ft.Colors.GREY, italic=True),
                    padding=20,
                )
            )

        history_list.controls = controls
        page.update()

    def show_month_detail(month_id: int):
        expenses = get_expenses(month_id)
        m = get_month(month_id)
        if not m:
            return
        label = get_month_label(m.year, m.month)
        total = get_month_total(month_id)

        items = []
        for exp in expenses:
            note_text = exp.note if exp.note else ""
            desc = f"{exp.category}{' - ' + note_text if note_text else ''}"
            items.append(
                ft.ListTile(
                    title=ft.Text(desc, size=14),
                    subtitle=ft.Text(exp.date.strftime("%b %d, %Y"), size=12, color=ft.Colors.GREY_600),
                    trailing=ft.Text(f"₹{exp.amount:,.2f}", size=14, weight=ft.FontWeight.W_600),
                    dense=True,
                )
            )

        if not items:
            items.append(ft.Text("No expenses", color=ft.Colors.GREY, italic=True))

        dlg = ft.AlertDialog(
            title=ft.Text(f"{label} — ₹{total:,.2f}", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dialog(dlg))],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def show_main_view():
        main_body.visible = True
        history_view.visible = False
        page.appbar.title = ft.Text(get_month_label(active_month.year, active_month.month), size=22, weight=ft.FontWeight.BOLD)
        page.appbar.actions = [
            ft.IconButton(icon=ft.Icons.LIST_ALT, tooltip="History", on_click=open_history),
        ]
        refresh_expenses()
        page.update()

    def open_history(e):
        build_history()
        main_body.visible = False
        history_view.visible = True
        page.appbar.title = ft.Text("History", size=22, weight=ft.FontWeight.BOLD)
        page.appbar.actions = [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Back", on_click=lambda e: show_main_view()),
        ]
        page.update()

    main_body = ft.Column(
        controls=[
            input_form,
            ft.Divider(height=1),
            expense_list,
            ft.Divider(height=1),
            total_text,
            footer_row,
        ],
        expand=True,
        spacing=10,
    )

    history_view = ft.Column(
        controls=[
            history_list,
        ],
        expand=True,
        spacing=10,
        visible=False,
    )

    page.appbar = ft.AppBar(
        title=ft.Text(get_month_label(active_month.year, active_month.month), size=22, weight=ft.FontWeight.BOLD),
        center_title=False,
        actions=[
            ft.IconButton(icon=ft.Icons.LIST_ALT, tooltip="History", on_click=open_history),
        ],
    )

    body = ft.Stack(
        controls=[main_body, history_view],
        expand=True,
    )

    page.add(body)

    refresh_expenses()


ft.app(target=main)
