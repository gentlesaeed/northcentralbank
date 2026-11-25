import hashlib
import secrets
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk


BLUE = "#176B4B"
DARK = "#172B4D"
WHITE = "#FFFFFF"
BG = "#F4F6FA"
GREY = "#7B8798"
GREEN = "#168A68"
ORANGE = "#D97706"
RED = "#C24141"
GREEN_TINT = "#EAF5EF"
GREEN_BORDER = "#D3E8DA"


def is_currency_amount(amount: Decimal) -> bool:
    if not amount.is_finite():
        return False
    try:
        return amount == amount.quantize(Decimal("0.01"))
    except InvalidOperation:
        return False


@dataclass
class Account:
    number: str
    name: str
    balance: Decimal
    account_type: str = "Checking"


@dataclass
class Transaction:
    created_at: datetime
    kind: str
    source: str
    destination: str
    amount: Decimal


@dataclass
class LoanApplication:
    created_at: datetime
    loan_type: str
    amount: Decimal
    purpose: str
    term: str
    status: str = "Submitted"


class BankLedger:
    def __init__(self):
        self.accounts: dict[str, Account] = {}
        self.transactions: list[Transaction] = []

    def create_account(
        self, name: str, opening_balance: Decimal, account_type: str = "Checking"
    ) -> Account:
        name = name.strip()
        if not name:
            raise ValueError("Enter the account holder's name.")
        if not is_currency_amount(opening_balance) or opening_balance < 0:
            raise ValueError("Opening balance must be zero or more, with no more than two decimal places.")
        if account_type not in {"Checking", "Savings"}:
            raise ValueError("Choose Checking or Savings for the account type.")

        number = str(secrets.randbelow(900000) + 100000)
        while number in self.accounts:
            number = str(secrets.randbelow(900000) + 100000)

        account = Account(number, name, opening_balance, account_type)
        self.accounts[number] = account
        if opening_balance:
            self.transactions.append(
                Transaction(datetime.now(), "Opening deposit", "—", number, opening_balance)
            )
        return account

    def transfer(self, source: str, destination: str, amount: Decimal) -> Transaction:
        if source not in self.accounts or destination not in self.accounts:
            raise ValueError("Select valid source and destination accounts.")
        if source == destination:
            raise ValueError("Choose two different accounts.")
        if not is_currency_amount(amount) or amount <= 0:
            raise ValueError("Transfer amount must be positive, with no more than two decimal places.")
        if self.accounts[source].balance < amount:
            raise ValueError("The source account does not have enough funds.")

        self.accounts[source].balance -= amount
        self.accounts[destination].balance += amount
        transaction = Transaction(datetime.now(), "Transfer", source, destination, amount)
        self.transactions.append(transaction)
        return transaction

    @property
    def total_balance(self) -> Decimal:
        return sum((account.balance for account in self.accounts.values()), Decimal("0"))

    @property
    def total_transferred(self) -> Decimal:
        return sum(
            (transaction.amount for transaction in self.transactions if transaction.kind == "Transfer"),
            Decimal("0"),
        )


class BankApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.ledger = BankLedger()
        self.loan_applications: list[LoanApplication] = []
        self.two_factor_enabled = False
        self.password_salt: bytes | None = None
        self.password_hash: bytes | None = None
        self.password_updated_at: datetime | None = None
        self.last_login = datetime.now()
        self.account_tier = "Basic"
        self.pending_upgrade: str | None = None
        self.page_buttons: dict[str, tk.Button] = {}
        self.root.title("North Central Bank")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)
        self._configure_styles()
        self._build_shell()
        self.show_page("dashboard")

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=32, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", GREEN_TINT)], foreground=[("selected", DARK)])
        style.configure("TCombobox", padding=7)

    def _build_shell(self):
        sidebar = tk.Frame(self.root, bg=WHITE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="NORTH CENTRAL",
            font=("Arial", 16, "bold"),
            bg=WHITE,
            fg=BLUE,
        ).pack(pady=(30, 28))

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg=WHITE, height=75)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.heading = tk.Label(
            self.header,
            text="",
            font=("Arial", 23, "bold"),
            bg=WHITE,
            fg=DARK,
        )
        self.heading.pack(side="left", padx=30, pady=18)

        self.content = tk.Frame(self.main, bg=BG)
        self.content.pack(fill="both", expand=True)
        self.footer = tk.Label(
            self.main,
            text="North Central Bank | Local simulation — data is not saved after closing",
            font=("Arial", 9),
            bg=BG,
            fg=GREY,
        )
        self.footer.pack(pady=8)

        pages = [
            ("dashboard", "Dashboard"),
            ("transactions", "Transactions"),
            ("accounts", "Accounts"),
            ("transfers", "Transfers"),
            ("checking_savings", "Checking & Savings"),
            ("loans", "Loans"),
            ("upgrade", "Account Upgrade"),
            ("security", "Security"),
            ("reports", "Reports"),
            ("settings", "Settings"),
        ]
        for key, label in pages:
            button = tk.Button(
                sidebar,
                text=label,
                font=("Arial", 11),
                bg=WHITE,
                fg=DARK,
                activebackground=GREEN_TINT,
                activeforeground=BLUE,
                relief="flat",
                anchor="w",
                padx=20,
                pady=12,
                command=lambda page=key: self.show_page(page),
            )
            button.pack(fill="x", padx=8, pady=3)
            self.page_buttons[key] = button

        tk.Button(
            sidebar,
            text="Logout",
            font=("Arial", 11),
            bg=WHITE,
            fg=DARK,
            activebackground="#FDECEC",
            relief="flat",
            anchor="w",
            padx=20,
            pady=12,
            command=self.logout,
        ).pack(side="bottom", fill="x", padx=8, pady=12)

    def show_page(self, page: str):
        page_titles = {
            "dashboard": "Overview",
            "transactions": "Transactions",
            "accounts": "Accounts",
            "transfers": "Transfers",
            "checking_savings": "Checking & Savings",
            "loans": "Loans",
            "upgrade": "Account Upgrade",
            "security": "Security",
            "reports": "Reports",
            "settings": "Settings",
        }
        self.heading.config(text=page_titles[page])
        for key, button in self.page_buttons.items():
            active = key == page
            button.config(bg=GREEN_TINT if active else WHITE, fg=BLUE if active else DARK)

        for child in self.content.winfo_children():
            child.destroy()
        getattr(self, f"_build_{page}")()

    def _section_title(self, parent: tk.Widget, text: str):
        tk.Label(
            parent,
            text=text,
            font=("Arial", 17, "bold"),
            bg=parent.cget("bg"),
            fg=DARK,
        ).pack(anchor="w", pady=(0, 14))

    def _card(self, parent: tk.Widget, title: str, value: str, color: str = BLUE):
        card = tk.Frame(
            parent,
            bg=WHITE,
            padx=20,
            pady=18,
            highlightbackground="#E2E8F0",
            highlightthickness=1,
        )
        card.pack(side="left", expand=True, fill="x", padx=8)
        tk.Label(card, text=title, font=("Arial", 10), bg=WHITE, fg=GREY).pack(anchor="w")
        tk.Label(card, text=value, font=("Arial", 21, "bold"), bg=WHITE, fg=color).pack(
            anchor="w", pady=(9, 0)
        )

    def _make_table(self, parent: tk.Widget, columns: tuple, headings: tuple, widths: tuple):
        table_frame = tk.Frame(parent, bg=WHITE)
        table_frame.pack(fill="both", expand=True)
        table = ttk.Treeview(table_frame, columns=columns, show="headings")
        for column, heading, width in zip(columns, headings, widths):
            table.heading(column, text=heading)
            table.column(column, width=width, minwidth=80, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return table

    @staticmethod
    def _money(amount: Decimal) -> str:
        return f"${amount:,.2f}"

    @staticmethod
    def _parse_amount(value: str, allow_zero: bool = False) -> Decimal:
        try:
            amount = Decimal(value.strip().replace(",", "").replace("$", ""))
        except InvalidOperation as error:
            raise ValueError("Enter a valid amount, for example 125.50.") from error
        if not is_currency_amount(amount):
            raise ValueError("Enter an amount with no more than two decimal places.")
        if amount < 0 or (amount == 0 and not allow_zero):
            qualifier = "zero or more" if allow_zero else "greater than zero"
            raise ValueError(f"Amount must be {qualifier}.")
        return amount

    def _build_dashboard(self):
        page = self.content
        tk.Label(
            page,
            text="Welcome to North Central Bank",
            font=("Arial", 18, "bold"),
            bg=BG,
            fg=DARK,
        ).pack(anchor="w", padx=30, pady=(24, 6))
        tk.Label(
            page,
            text="Manage accounts and move funds between customers.",
            font=("Arial", 10),
            bg=BG,
            fg=GREY,
        ).pack(anchor="w", padx=30)

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=22, pady=20)
        self._card(cards, "Total account balance", self._money(self.ledger.total_balance))
        self._card(cards, "Accounts", str(len(self.ledger.accounts)), GREEN)
        self._card(cards, "Transfers completed", str(sum(
            transaction.kind == "Transfer" for transaction in self.ledger.transactions
        )), ORANGE)

        panel = tk.Frame(page, bg=WHITE, padx=22, pady=18)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 18))
        self._section_title(panel, "Recent activity")
        table = self._make_table(
            panel,
            ("date", "type", "source", "destination", "amount"),
            ("Date", "Type", "From", "To", "Amount"),
            (150, 150, 130, 130, 120),
        )
        self._populate_transactions(table, limit=8)

    def _build_accounts(self):
        page = self.content
        panel = tk.Frame(page, bg=WHITE, padx=22, pady=18)
        panel.pack(fill="x", padx=30, pady=22)
        self._section_title(panel, "Create an account")

        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x")
        name_entry = self._form_field(form, "Account holder", 0)
        balance_entry = self._form_field(form, "Opening balance", 1)
        balance_entry.insert(0, "0.00")
        tk.Label(
            form, text="Account type", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK
        ).grid(row=0, column=2, sticky="w", pady=(0, 6))
        account_type_box = ttk.Combobox(
            form, values=("Checking", "Savings"), state="readonly", width=18
        )
        account_type_box.grid(row=1, column=2, padx=(0, 14), sticky="w")
        account_type_box.current(0)
        status = tk.Label(panel, text="", bg=WHITE, fg=RED, font=("Arial", 10))
        status.pack(anchor="w", pady=(8, 0))

        def create_account():
            try:
                opening_balance = self._parse_amount(balance_entry.get(), allow_zero=True)
                account = self.ledger.create_account(
                    name_entry.get(), opening_balance, account_type_box.get()
                )
            except ValueError as error:
                status.config(text=str(error), fg=RED)
                return
            status.config(
                text=f"{account.account_type} account created. Account number: {account.number}",
                fg=GREEN,
            )
            name_entry.delete(0, "end")
            balance_entry.delete(0, "end")
            balance_entry.insert(0, "0.00")
            self._refresh_accounts_table()

        tk.Button(
            form,
            text="Create account",
            command=create_account,
            bg=BLUE,
            fg=WHITE,
            activebackground="#10563B",
            activeforeground=WHITE,
            relief="flat",
            padx=18,
            pady=9,
        ).grid(row=1, column=3, padx=(0, 0), sticky="w")

        listing = tk.Frame(page, bg=WHITE, padx=22, pady=18)
        listing.pack(fill="both", expand=True, padx=30, pady=(0, 18))
        self._section_title(listing, "Account directory")
        self.accounts_table = self._make_table(
            listing,
            ("number", "name", "type", "balance"),
            ("Account number", "Account holder", "Type", "Balance"),
            (180, 270, 120, 160),
        )
        self._refresh_accounts_table()

    def _form_field(self, parent: tk.Widget, label: str, column: int):
        wrapper = tk.Frame(parent, bg=WHITE)
        wrapper.grid(row=0, column=column, padx=(0, 14), sticky="w")
        tk.Label(wrapper, text=label, font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).pack(
            anchor="w", pady=(0, 6)
        )
        entry = tk.Entry(wrapper, font=("Arial", 11), relief="solid", bd=1, width=25)
        entry.pack(ipady=7)
        return entry

    def _refresh_accounts_table(self):
        if not hasattr(self, "accounts_table") or not self.accounts_table.winfo_exists():
            return
        for item in self.accounts_table.get_children():
            self.accounts_table.delete(item)
        for account in self.ledger.accounts.values():
            self.accounts_table.insert(
                "",
                "end",
                values=(
                    account.number,
                    account.name,
                    account.account_type,
                    self._money(account.balance),
                ),
            )

    def _build_transfers(self):
        page = self.content
        panel = tk.Frame(page, bg=WHITE, padx=24, pady=22)
        panel.pack(fill="x", padx=30, pady=24)
        self._section_title(panel, "Transfer between accounts")

        if len(self.ledger.accounts) < 2:
            tk.Label(
                panel,
                text="Create at least two accounts before making a transfer.",
                font=("Arial", 11),
                bg=WHITE,
                fg=GREY,
            ).pack(anchor="w", pady=(0, 16))
            tk.Button(
                panel,
                text="Go to Accounts",
                command=lambda: self.show_page("accounts"),
                bg=BLUE,
                fg=WHITE,
                relief="flat",
                padx=16,
                pady=9,
            ).pack(anchor="w")
            return

        accounts = list(self.ledger.accounts.values())
        account_options = [f"{account.number} — {account.name}" for account in accounts]
        account_numbers = {option: option.split(" — ", 1)[0] for option in account_options}
        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x")

        tk.Label(form, text="From account", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        source_box = ttk.Combobox(form, values=account_options, state="readonly", width=34)
        source_box.grid(row=1, column=0, padx=(0, 20), sticky="w")
        source_box.current(0)

        tk.Label(form, text="To account", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=1, sticky="w", pady=(0, 6)
        )
        destination_box = ttk.Combobox(form, values=account_options, state="readonly", width=34)
        destination_box.grid(row=1, column=1, padx=(0, 20), sticky="w")
        destination_box.current(1)

        amount_entry = self._form_field(form, "Amount", 2)
        status = tk.Label(panel, text="", bg=WHITE, fg=RED, font=("Arial", 10))
        status.pack(anchor="w", pady=(12, 0))

        def submit_transfer():
            try:
                amount = self._parse_amount(amount_entry.get())
                transaction = self.ledger.transfer(
                    account_numbers[source_box.get()],
                    account_numbers[destination_box.get()],
                    amount,
                )
            except (ValueError, KeyError) as error:
                status.config(text=str(error), fg=RED)
                return
            messagebox.showinfo(
                "Transfer complete",
                f"{self._money(transaction.amount)} transferred successfully.",
                parent=self.root,
            )
            self.show_page("transactions")

        tk.Button(
            panel,
            text="Transfer funds",
            command=submit_transfer,
            bg=BLUE,
            fg=WHITE,
            activebackground="#10563B",
            activeforeground=WHITE,
            relief="flat",
            padx=18,
            pady=10,
        ).pack(anchor="w", pady=(16, 0))

    def _build_checking_savings(self):
        page = self.content
        checking_accounts = [
            account for account in self.ledger.accounts.values()
            if account.account_type == "Checking"
        ]
        savings_accounts = [
            account for account in self.ledger.accounts.values()
            if account.account_type == "Savings"
        ]
        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=22, pady=(18, 12))
        checking_total = sum((account.balance for account in checking_accounts), Decimal("0"))
        savings_total = sum((account.balance for account in savings_accounts), Decimal("0"))
        self._card(cards, "Checking balance", self._money(checking_total), BLUE)
        self._card(cards, "Savings balance", self._money(savings_total), GREEN)

        listing = tk.Frame(page, bg=WHITE, padx=22, pady=16)
        listing.pack(fill="both", expand=True, padx=30, pady=(0, 12))
        self._section_title(listing, "Checking and savings accounts")
        table = self._make_table(
            listing,
            ("type", "number", "holder", "balance"),
            ("Account type", "Account number", "Account holder", "Balance"),
            (150, 170, 250, 140),
        )
        for account in self.ledger.accounts.values():
            table.insert(
                "",
                "end",
                values=(
                    account.account_type,
                    account.number,
                    account.name,
                    self._money(account.balance),
                ),
            )

        transfer_panel = tk.Frame(page, bg=WHITE, padx=22, pady=16)
        transfer_panel.pack(fill="x", padx=30, pady=(0, 12))
        self._section_title(transfer_panel, "Move money between your accounts")
        eligible_accounts = [*checking_accounts, *savings_accounts]
        account_options = {
            f"{account.number} — {account.name} ({account.account_type})": account
            for account in eligible_accounts
        }
        status = tk.Label(transfer_panel, text="", bg=WHITE, fg=RED, font=("Arial", 10))
        if not checking_accounts or not savings_accounts:
            tk.Label(
                transfer_panel,
                text="Create at least one checking and one savings account for the same account holder to transfer between them.",
                font=("Arial", 10),
                bg=WHITE,
                fg=GREY,
                wraplength=850,
                justify="left",
            ).pack(anchor="w")
        else:
            form = tk.Frame(transfer_panel, bg=WHITE)
            form.pack(fill="x")
            tk.Label(form, text="From", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
                row=0, column=0, sticky="w", pady=(0, 6)
            )
            source_box = ttk.Combobox(
                form, values=tuple(account_options), state="readonly", width=34
            )
            source_box.grid(row=1, column=0, padx=(0, 12), sticky="w")
            tk.Label(form, text="To", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
                row=0, column=1, sticky="w", pady=(0, 6)
            )
            destination_box = ttk.Combobox(form, state="readonly", width=34)
            destination_box.grid(row=1, column=1, padx=(0, 12), sticky="w")
            amount_entry = self._form_field(form, "Amount", 2)

            def update_destinations(_event=None):
                _ = _event
                source_account = account_options.get(source_box.get())
                if source_account is None:
                    return
                destinations = [
                    option
                    for option, account in account_options.items()
                    if account.name.casefold() == source_account.name.casefold()
                    and account.account_type != source_account.account_type
                ]
                destination_box.configure(values=destinations)
                if destinations:
                    destination_box.current(0)
                else:
                    destination_box.set("")
                    status.config(
                        text="No matching account of the other type belongs to this holder.",
                        fg=RED,
                    )

            source_box.bind("<<ComboboxSelected>>", update_destinations)
            source_box.current(0)
            update_destinations()
            status.pack(anchor="w", pady=(8, 0))

            def submit_account_transfer():
                source = account_options.get(source_box.get())
                destination = account_options.get(destination_box.get())
                if source is None or destination is None:
                    status.config(text="Select a valid checking/savings pair.", fg=RED)
                    return
                if (
                    source.name.casefold() != destination.name.casefold()
                    or source.account_type == destination.account_type
                ):
                    status.config(
                        text="Transfers must be between checking and savings accounts for the same holder.",
                        fg=RED,
                    )
                    return
                try:
                    amount = self._parse_amount(amount_entry.get())
                    transaction = self.ledger.transfer(source.number, destination.number, amount)
                except ValueError as error:
                    status.config(text=str(error), fg=RED)
                    return
                messagebox.showinfo(
                    "Transfer complete",
                    f"{self._money(transaction.amount)} transferred successfully.",
                    parent=self.root,
                )
                self.show_page("checking_savings")

            tk.Button(
                form,
                text="Transfer",
                command=submit_account_transfer,
                bg=BLUE,
                fg=WHITE,
                activebackground="#10563B",
                activeforeground=WHITE,
                relief="flat",
                padx=16,
                pady=9,
            ).grid(row=1, column=3, sticky="w")

        activity = tk.Frame(page, bg=WHITE, padx=22, pady=14)
        activity.pack(fill="both", expand=True, padx=30, pady=(0, 14))
        self._section_title(activity, "Recent activity")
        table = self._make_table(
            activity,
            ("date", "type", "source", "destination", "amount"),
            ("Date", "Type", "From", "To", "Amount"),
            (150, 130, 120, 120, 110),
        )
        for transaction in reversed(self.ledger.transactions[-6:]):
            table.insert(
                "",
                "end",
                values=(
                    transaction.created_at.strftime("%Y-%m-%d %H:%M"),
                    transaction.kind,
                    transaction.source,
                    transaction.destination,
                    self._money(transaction.amount),
                ),
            )

    def _build_loans(self):
        page = self.content
        options = (
            ("Personal loan", "8.9% APR", "Unsecured borrowing for planned expenses."),
            ("Home improvement", "7.4% APR", "A fixed-term loan for home projects."),
            ("Auto loan", "6.9% APR", "Financing for a new or used vehicle."),
        )
        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=22, pady=(18, 12))
        for title, apr, detail in options:
            card = tk.Frame(
                cards,
                bg=WHITE,
                padx=18,
                pady=14,
                highlightbackground=GREEN_BORDER,
                highlightthickness=1,
            )
            card.pack(side="left", expand=True, fill="both", padx=8)
            tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=WHITE, fg=BLUE).pack(
                anchor="w"
            )
            tk.Label(card, text=apr, font=("Arial", 16, "bold"), bg=WHITE, fg=GREEN).pack(
                anchor="w", pady=(7, 3)
            )
            tk.Label(
                card, text=detail, font=("Arial", 9), bg=WHITE, fg=GREY, wraplength=230
            ).pack(anchor="w")

        panel = tk.Frame(page, bg=WHITE, padx=22, pady=16)
        panel.pack(fill="x", padx=30, pady=(0, 12))
        self._section_title(panel, "Check details and submit a request")
        tk.Label(
            panel,
            text="Sample rates and terms for this local demo only.",
            font=("Arial", 9),
            bg=WHITE,
            fg=GREY,
        ).pack(anchor="w", pady=(0, 10))
        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x")
        loan_type = ttk.Combobox(
            form, values=tuple(option[0] for option in options), state="readonly", width=22
        )
        loan_type.current(0)
        tk.Label(form, text="Loan option", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        loan_type.grid(row=1, column=0, padx=(0, 12), sticky="w")
        amount_entry = self._form_field(form, "Amount ($500–$50,000)", 1)
        purpose_entry = self._form_field(form, "Purpose", 2)
        term_box = ttk.Combobox(
            form, values=("12 months", "24 months", "36 months", "60 months"),
            state="readonly", width=16
        )
        term_box.current(1)
        tk.Label(form, text="Term", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=3, sticky="w", pady=(0, 6)
        )
        term_box.grid(row=1, column=3, padx=(0, 12), sticky="w")
        status = tk.Label(panel, text="", bg=WHITE, fg=RED, font=("Arial", 10))
        status.pack(anchor="w", pady=(8, 0))

        def submit_loan_request():
            if not any(
                account.account_type == "Checking"
                for account in self.ledger.accounts.values()
            ):
                status.config(
                    text="Eligibility check: create a checking account before requesting a loan.",
                    fg=RED,
                )
                return
            try:
                amount = self._parse_amount(amount_entry.get())
            except ValueError as error:
                status.config(text=str(error), fg=RED)
                return
            if amount < Decimal("500") or amount > Decimal("50000"):
                status.config(text="Loan requests must be between $500 and $50,000.", fg=RED)
                return
            purpose = purpose_entry.get().strip()
            if not purpose:
                status.config(text="Enter a brief purpose for the loan request.", fg=RED)
                return
            application = LoanApplication(
                datetime.now(), loan_type.get(), amount, purpose, term_box.get()
            )
            self.loan_applications.append(application)
            status.config(
                text="Request submitted for review. This demo does not perform credit checks or approve loans.",
                fg=GREEN,
            )
            amount_entry.delete(0, "end")
            purpose_entry.delete(0, "end")
            self._refresh_loan_table()

        tk.Button(
            form,
            text="Submit request",
            command=submit_loan_request,
            bg=BLUE,
            fg=WHITE,
            activebackground="#10563B",
            activeforeground=WHITE,
            relief="flat",
            padx=14,
            pady=9,
        ).grid(row=1, column=4, sticky="w")

        history = tk.Frame(page, bg=WHITE, padx=22, pady=14)
        history.pack(fill="both", expand=True, padx=30, pady=(0, 14))
        self._section_title(history, "Loan requests")
        self.loan_table = self._make_table(
            history,
            ("date", "loan", "amount", "term", "status"),
            ("Date", "Loan option", "Amount", "Term", "Status"),
            (150, 190, 130, 110, 120),
        )
        self._refresh_loan_table()

    def _refresh_loan_table(self):
        if not hasattr(self, "loan_table") or not self.loan_table.winfo_exists():
            return
        for item in self.loan_table.get_children():
            self.loan_table.delete(item)
        for application in reversed(self.loan_applications):
            self.loan_table.insert(
                "",
                "end",
                values=(
                    application.created_at.strftime("%Y-%m-%d"),
                    application.loan_type,
                    self._money(application.amount),
                    application.term,
                    application.status,
                ),
            )

    def _build_upgrade(self):
        page = self.content
        tiers = (
            ("Basic", Decimal("0"), "Standard digital banking and account access."),
            ("Plus", Decimal("5000"), "Priority support and an improved savings rate."),
            ("Premier", Decimal("25000"), "Dedicated support and premium account benefits."),
        )
        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=22, pady=(18, 12))
        for tier, minimum, benefits in tiers:
            card = tk.Frame(
                cards,
                bg=WHITE,
                padx=18,
                pady=16,
                highlightbackground=GREEN_BORDER,
                highlightthickness=1,
            )
            card.pack(side="left", expand=True, fill="both", padx=8)
            tier_label = tier + ("  • CURRENT" if tier == self.account_tier else "")
            tk.Label(card, text=tier_label, font=("Arial", 13, "bold"), bg=WHITE, fg=BLUE).pack(
                anchor="w"
            )
            tk.Label(
                card,
                text=f"Minimum balance: {self._money(minimum)}",
                font=("Arial", 10, "bold"),
                bg=WHITE,
                fg=GREEN,
            ).pack(anchor="w", pady=(8, 4))
            tk.Label(
                card, text=benefits, font=("Arial", 9), bg=WHITE, fg=GREY, wraplength=220
            ).pack(anchor="w")

        panel = tk.Frame(page, bg=WHITE, padx=24, pady=20)
        panel.pack(fill="x", padx=30, pady=(0, 14))
        self._section_title(panel, "Request an account upgrade")
        tk.Label(
            panel,
            text="Benefits and balance thresholds below are illustrative demo requirements.",
            font=("Arial", 9),
            bg=WHITE,
            fg=GREY,
        ).pack(anchor="w", pady=(0, 10))
        balance = self.ledger.total_balance
        checking_exists = any(
            account.account_type == "Checking" for account in self.ledger.accounts.values()
        )
        tk.Label(
            panel,
            text=(
                f"Current tier: {self.account_tier}  •  Total balance: {self._money(balance)}"
                f"  •  Checking account: {'Yes' if checking_exists else 'No'}"
            ),
            font=("Arial", 10),
            bg=WHITE,
            fg=DARK,
        ).pack(anchor="w", pady=(0, 12))

        tier_order = {"Basic": 0, "Plus": 1, "Premier": 2}
        available_tiers = [
            tier_data[0] for tier_data in tiers
            if tier_order[tier_data[0]] > tier_order[self.account_tier]
        ]
        if not available_tiers:
            tk.Label(
                panel, text="You are on the highest available tier.", bg=WHITE, fg=GREEN
            ).pack(anchor="w")
            return
        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x")
        tk.Label(
            form, text="Upgrade to", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        tier_box = ttk.Combobox(form, values=available_tiers, state="readonly", width=18)
        tier_box.current(0)
        tier_box.grid(row=1, column=0, padx=(0, 16), sticky="w")
        requirement = tk.Label(panel, text="", bg=WHITE, fg=GREY, font=("Arial", 10))
        requirement.pack(anchor="w", pady=(12, 0))
        status = tk.Label(panel, text="", bg=WHITE, fg=GREEN, font=("Arial", 10))
        status.pack(anchor="w", pady=(8, 0))

        def update_requirement(_event=None):
            _ = _event
            selected = tier_box.get()
            minimum = next(tier_data[1] for tier_data in tiers if tier_data[0] == selected)
            balance_ok = balance >= minimum
            checking_ok = checking_exists
            requirement.config(
                text=(
                    f"Requirements: balance {self._money(balance)} / {self._money(minimum)} "
                    f"({'met' if balance_ok else 'not met'}); checking account "
                    f"({'met' if checking_ok else 'required'})."
                ),
                fg=GREEN if balance_ok and checking_ok else ORANGE,
            )

        tier_box.bind("<<ComboboxSelected>>", update_requirement)
        update_requirement()

        def request_upgrade():
            selected = tier_box.get()
            minimum = next(tier_data[1] for tier_data in tiers if tier_data[0] == selected)
            if balance < minimum:
                status.config(
                    text=f"Reach a total balance of {self._money(minimum)} before requesting this tier.",
                    fg=RED,
                )
                return
            if not checking_exists:
                status.config(text="Create a checking account before requesting an upgrade.", fg=RED)
                return
            if self.pending_upgrade is not None:
                status.config(
                    text=f"Your {self.pending_upgrade} upgrade request is already pending.",
                    fg=ORANGE,
                )
                return
            self.pending_upgrade = selected
            status.config(
                text=f"{selected} upgrade request submitted for review. Your current tier remains {self.account_tier}.",
                fg=GREEN,
            )

        tk.Button(
            form,
            text="Request upgrade",
            command=request_upgrade,
            bg=BLUE,
            fg=WHITE,
            activebackground="#10563B",
            activeforeground=WHITE,
            relief="flat",
            padx=16,
            pady=9,
        ).grid(row=1, column=1, sticky="w")
        if self.pending_upgrade is not None:
            status.config(
                text=f"Pending request: {self.pending_upgrade}. Tier changes require review.",
                fg=ORANGE,
            )

    def _build_security(self):
        panel = tk.Frame(self.content, bg=WHITE, padx=24, pady=20)
        panel.pack(fill="x", padx=30, pady=(22, 14))
        self._section_title(panel, "Password settings")
        tk.Label(
            panel,
            text="Set a new password for this local demo. There is no sign-in service or server-side account.",
            font=("Arial", 10),
            bg=WHITE,
            fg=GREY,
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x")
        tk.Label(form, text="New password", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        password_entry = tk.Entry(form, font=("Arial", 11), show="*", relief="solid", bd=1, width=28)
        password_entry.grid(row=1, column=0, padx=(0, 14), ipady=7, sticky="w")
        tk.Label(
            form, text="Confirm password", font=("Arial", 10, "bold"), bg=WHITE, fg=DARK
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))
        confirm_entry = tk.Entry(form, font=("Arial", 11), show="*", relief="solid", bd=1, width=28)
        confirm_entry.grid(row=1, column=1, padx=(0, 14), ipady=7, sticky="w")
        password_status = tk.Label(panel, text="", bg=WHITE, fg=RED, font=("Arial", 10))
        password_status.pack(anchor="w", pady=(9, 0))

        def update_password():
            new_password = password_entry.get()
            if len(new_password) < 8:
                password_status.config(text="Password must be at least 8 characters.", fg=RED)
                return
            if new_password != confirm_entry.get():
                password_status.config(text="The password entries do not match.", fg=RED)
                return
            self.password_salt = secrets.token_bytes(16)
            self.password_hash = hashlib.pbkdf2_hmac(
                "sha256", new_password.encode("utf-8"), self.password_salt, 200000
            )
            self.password_updated_at = datetime.now()
            password_entry.delete(0, "end")
            confirm_entry.delete(0, "end")
            password_status.config(
                text="Demo password updated in memory for this session only.", fg=GREEN
            )
            recent_status_label.config(
                text=(
                    f"Session started: {self.last_login.strftime('%Y-%m-%d %H:%M')}    •    "
                    f"Password last updated: {self.password_updated_at.strftime('%Y-%m-%d %H:%M')}    •    "
                    "No failed sign-ins recorded (local demo)."
                )
            )

        tk.Button(
            form,
            text="Update password",
            command=update_password,
            bg=BLUE,
            fg=WHITE,
            activebackground="#10563B",
            activeforeground=WHITE,
            relief="flat",
            padx=16,
            pady=9,
        ).grid(row=1, column=2, sticky="w")

        security_panel = tk.Frame(self.content, bg=WHITE, padx=24, pady=20)
        security_panel.pack(fill="x", padx=30, pady=(0, 16))
        self._section_title(security_panel, "Two-factor authentication")
        tk.Label(
            security_panel,
            text="Toggle a demo preference only; no verification codes are sent.",
            font=("Arial", 10),
            bg=WHITE,
            fg=GREY,
        ).pack(anchor="w", pady=(0, 10))
        two_factor_var = tk.BooleanVar(value=self.two_factor_enabled)

        def toggle_two_factor():
            self.two_factor_enabled = two_factor_var.get()
            security_status.config(
                text=(
                    f"Two-factor preference: {'On' if self.two_factor_enabled else 'Off'} "
                    " (demo only)"
                ),
                fg=GREEN if self.two_factor_enabled else GREY,
            )

        tk.Checkbutton(
            security_panel,
            text="Enable two-factor preference",
            variable=two_factor_var,
            command=toggle_two_factor,
            bg=WHITE,
            fg=DARK,
            activebackground=WHITE,
            selectcolor=GREEN_TINT,
            font=("Arial", 10),
        ).pack(anchor="w")
        security_status = tk.Label(
            security_panel,
            text=f"Two-factor preference: {'On' if self.two_factor_enabled else 'Off'} (demo only)",
            bg=WHITE,
            fg=GREEN if self.two_factor_enabled else GREY,
            font=("Arial", 10),
        )
        security_status.pack(anchor="w", pady=(8, 0))

        status_panel = tk.Frame(self.content, bg=WHITE, padx=24, pady=18)
        status_panel.pack(fill="x", padx=30, pady=(0, 18))
        self._section_title(status_panel, "Recent security status")
        password_text = (
            f"Password last updated: {self.password_updated_at.strftime('%Y-%m-%d %H:%M')}"
            if self.password_updated_at
            else "Password: not set in this session"
        )
        recent_status_label = tk.Label(
            status_panel,
            text=(
                f"Session started: {self.last_login.strftime('%Y-%m-%d %H:%M')}    •    "
                f"{password_text}    •    No failed sign-ins recorded (local demo)."
            ),
            font=("Arial", 10),
            bg=WHITE,
            fg=DARK,
            wraplength=850,
            justify="left",
        )
        recent_status_label.pack(anchor="w")

    def _build_transactions(self):
        panel = tk.Frame(self.content, bg=WHITE, padx=22, pady=18)
        panel.pack(fill="both", expand=True, padx=30, pady=22)
        self._section_title(panel, "Transaction history")
        table = self._make_table(
            panel,
            ("date", "type", "source", "destination", "amount"),
            ("Date", "Type", "From", "To", "Amount"),
            (170, 160, 150, 150, 130),
        )
        self._populate_transactions(table)

    def _populate_transactions(self, table: ttk.Treeview, limit: int | None = None):
        transactions = list(reversed(self.ledger.transactions))
        if limit is not None:
            transactions = transactions[:limit]
        for transaction in transactions:
            table.insert(
                "",
                "end",
                values=(
                    transaction.created_at.strftime("%Y-%m-%d %H:%M"),
                    transaction.kind,
                    transaction.source,
                    transaction.destination,
                    self._money(transaction.amount),
                ),
            )

    def _build_reports(self):
        page = self.content
        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=22, pady=22)
        self._card(cards, "Total account balance", self._money(self.ledger.total_balance))
        self._card(cards, "Total transferred", self._money(self.ledger.total_transferred), GREEN)
        self._card(
            cards,
            "Transactions recorded",
            str(len(self.ledger.transactions)),
            ORANGE,
        )

        panel = tk.Frame(page, bg=WHITE, padx=22, pady=18)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self._section_title(panel, "Balances by account")
        table = self._make_table(
            panel,
            ("number", "name", "balance"),
            ("Account number", "Account holder", "Current balance"),
            (180, 300, 170),
        )
        for account in self.ledger.accounts.values():
            table.insert("", "end", values=(account.number, account.name, self._money(account.balance)))

    def _build_settings(self):
        panel = tk.Frame(self.content, bg=WHITE, padx=24, pady=22)
        panel.pack(fill="x", padx=30, pady=24)
        self._section_title(panel, "About this application")
        tk.Label(
            panel,
            text=(
                "North Central Bank is a local banking simulation. Accounts and transactions "
                "exist only while the app is open. Loan and account-upgrade requests are not "
                "processed, security settings are demo-only, no real money moves, and no data is saved."
            ),
            font=("Arial", 11),
            bg=WHITE,
            fg=DARK,
            wraplength=800,
            justify="left",
        ).pack(anchor="w")

    def logout(self):
        if messagebox.askyesno("Exit", "Close North Central Bank?", parent=self.root):
            self.root.destroy()


def main():
    root = tk.Tk()
    BankApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
