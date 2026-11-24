import tkinter as tk

# main window
root = tk.Tk()
root.title("North central Bank")
root.geometry("1200x750")
root.configure(bg="#F4F6FA")

#Colours
BLUE  = "#2455D6"
DARK = "#172B4D"
WHITE = "#FFFFFF"
BG = "#F4F6FA"
GREY = "#7B8798"

#Sidebar
sidebar = tk.Frame(root, bg=WHITE, width=210)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# Bank name
bank_name = tk.Label(
    sidebar,
    text="🏦 NORTH CENTRAL",
    font=("Arial", 15, "bold"),
    bg=WHITE,
    fg=BLUE
)
bank_name.pack(pady=30)

# sidebar buttons
menu_items = [
    "🏠 Dashboard",
    "💳 Tansaction",
    "👤 Accounts",
    "💸 Transfers",
    "📊 Reports",
    "⚙️ settings",
    "🚪 Logout"
]

def menu_click(item):
    message.config(text=f"{item} selected")

for item in menu_items:
    button = tk.Button(
        sidebar,
        text=item,
        font=("Arial", 11),
        bg=WHITE,
        fg=DARK,
        relief="flat",
        anchor="w",
        padx=20,
        pady=12,
        command=lambda x=item: menu_click(x)
    )
    button.pack(fill="x", padx=8, pady=3)

# Main Content
main = tk.Frame(root, bg=BG)
main.pack(side="left", fill="both", expand=True)

dashboard_page = tk.Frame(main, bg=BG)
dashboard_page.pack(fill="both", expand=True)

# Header
header = tk.Frame(dashboard_page, bg=WHITE, height=75)
header.pack(fill="x")
header.pack_propagate(False)

heading = tk.Label(
    header,
    text="Overview",
    font=("Arial", 23, "bold"),
    bg=WHITE,
    fg=DARK
)
heading.pack(side="left", padx=30, pady=18)

# welcome message
welcome = tk.Label(
    dashboard_page,
    text="Welcome to North central Bank",
    font=("Arial", 17, "bold"),
    bg=BG,
    fg=DARK
)
welcome.pack(anchor="w", padx=30, pady=25)

# Message
message = tk.Label(
    dashboard_page,
    text="Your banking dashboard",
    font=("Arial", 10),
    bg=BG,
    fg=GREY
)
message.pack(anchor="w", padx=30)

# Accountcards
cards = tk.Frame( dashboard_page, bg=BG)
cards.pack(fill="x", padx=25, pady=20)

def create_card(title, value, color):
    card = tk.Frame(
        cards,
        bg=WHITE,
        padx=20,
        pady=25,
        highlightbackground="#E2E8F0",
        highlightthickness=1

    )
    card.pack(side="left", expand=True, fill="x", padx=8)

    tk.Label(
        card,
        text=title,
        font=("Arial", 11),
        bg= WHITE,
        fg=GREY
    ).pack(anchor="w")

    tk.Label(
        card,
        text=value,
        font=("Arial", 22, "bold"),
        bg=WHITE,
        fg=color
    ).pack(anchor="w", pady=12)

create_card("Account Balance", "$0.00", BLUE)
create_card("Total Deposit", "$0.00", "#16A085")
create_card("Total Withdrawals", "$0.00", "#E67E22")

# Recent transactions
transactions = tk.Frame(dashboard_page, bg=WHITE, padx=25, pady=20)
transactions.pack(fill="both", expand=True, padx=32, pady=20)

tk.Label(
    transactions,
    text="Recent Transactions",
    font=("Arial", 17, "bold"),
    bg=WHITE,
    fg=DARK
).pack(anchor="w", pady=10)

tk.Label(
    transactions,
    text="No transactions available yet.",
    font=("Arial", 12),
    bg=WHITE,
    fg=GREY
).pack(anchor="w", pady=20)

# Footer
footer = tk.Label(
    main,
    text="North Central Bank | Secure Banking Simulation",
    font=("Arial", 9),
    bg=BG,
    fg=GREY
)
footer.pack(pady=10)

root.mainloop()