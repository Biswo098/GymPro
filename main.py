import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pages.members import show_add_member
from pages.manage_members import show_manage_members
from pages.attendance import show_attendance
from pages.membership import show_membership
from pages.payments import show_payments
from pages.reports import show_reports
from backup import backup_database


# --------------------------------------------------
# APPLICATION PATH
# --------------------------------------------------

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(APP_DIR)


# --------------------------------------------------
# MAIN WINDOW
# --------------------------------------------------

root = tk.Tk()

root.title("GymPro - Gym Management System")
root.geometry("1200x750")
root.minsize(1050, 650)
root.configure(bg="#101827")


# --------------------------------------------------
# COLORS
# --------------------------------------------------

BG_COLOR = "#101827"
SIDEBAR_COLOR = "#172338"
CARD_COLOR = "#1E2D45"
ACCENT_COLOR = "#2563EB"
GREEN = "#16A34A"
ORANGE = "#F59E0B"
RED = "#EF4444"
TEXT_COLOR = "#FFFFFF"
MUTED_COLOR = "#A0AEC0"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    return sqlite3.connect("database/gym.db")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

sidebar = tk.Frame(
    root,
    bg=SIDEBAR_COLOR,
    width=230
)

sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)


logo = tk.Label(
    sidebar,
    text="GYMPRO",
    font=("Arial", 25, "bold"),
    bg=SIDEBAR_COLOR,
    fg=TEXT_COLOR
)

logo.pack(pady=(30, 5))


subtitle = tk.Label(
    sidebar,
    text="GYM MANAGEMENT",
    font=("Arial", 9),
    bg=SIDEBAR_COLOR,
    fg=MUTED_COLOR
)

subtitle.pack(pady=(0, 35))


# --------------------------------------------------
# MAIN CONTENT
# --------------------------------------------------

content = tk.Frame(
    root,
    bg=BG_COLOR
)

content.pack(side="right", fill="both", expand=True)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

def show_dashboard():

    # Clear previous page
    for widget in content.winfo_children():
        widget.destroy()

    today = date.today()
    today_string = today.isoformat()
    seven_days = (today + timedelta(days=7)).isoformat()

    # --------------------------------------------------
    # FETCH DATABASE STATISTICS
    # --------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM members
        """)

        total_members = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT m.member_id, ms.start_date, ms.end_date
                FROM members m
                JOIN memberships ms
                ON ms.membership_id = (
                    SELECT MAX(ms2.membership_id)
                    FROM memberships ms2
                    WHERE ms2.member_id = m.member_id
                )
            )
            WHERE start_date <= ?
            AND end_date >= ?
        """, (today_string, today_string))

        active_members = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT m.member_id, ms.end_date
                FROM members m
                JOIN memberships ms
                ON ms.membership_id = (
                    SELECT MAX(ms2.membership_id)
                    FROM memberships ms2
                    WHERE ms2.member_id = m.member_id
                )
            )
            WHERE end_date < ?
        """, (today_string,))

        expired_members = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE attendance_date = ?
            AND status = 'Present'
        """, (today_string,))

        today_attendance = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE payment_date = ?
        """, (today_string,))

        today_revenue = cursor.fetchone()[0]

        # Monthly revenue
        cursor.execute("""
            SELECT
                CAST(strftime('%m', payment_date) AS INTEGER),
                SUM(amount)
            FROM payments
            WHERE strftime('%Y', payment_date) = ?
            GROUP BY strftime('%m', payment_date)
        """, (str(today.year),))

        monthly_records = cursor.fetchall()

        # Recent payments
        cursor.execute("""
            SELECT m.name, p.amount,
                   p.payment_date, p.payment_method
            FROM payments p
            JOIN members m
            ON p.member_id = m.member_id
            ORDER BY p.payment_id DESC
            LIMIT 5
        """)

        recent_payments = cursor.fetchall()

        # Expiring memberships
        cursor.execute("""
            SELECT m.name, m.phone, ms.end_date
            FROM members m
            JOIN memberships ms
            ON ms.membership_id = (
                SELECT MAX(ms2.membership_id)
                FROM memberships ms2
                WHERE ms2.member_id = m.member_id
            )
            WHERE ms.start_date <= ?
            AND ms.end_date BETWEEN ? AND ?
            ORDER BY ms.end_date
        """, (today_string, today_string, seven_days))

        expiring_members = cursor.fetchall()

    finally:
        conn.close()

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    header_frame = tk.Frame(
        content,
        bg=BG_COLOR
    )

    header_frame.pack(
        fill="x",
        padx=25,
        pady=(20, 10)
    )

    tk.Label(
        header_frame,
        text="Dashboard",
        font=("Arial", 25, "bold"),
        bg=BG_COLOR,
        fg=TEXT_COLOR
    ).pack(side="left")

    tk.Label(
        header_frame,
        text=today.strftime("%A, %d %B %Y"),
        font=("Arial", 11),
        bg=BG_COLOR,
        fg=MUTED_COLOR
    ).pack(side="right", pady=10)

    tk.Label(
        content,
        text="Welcome back! Here's your gym's performance today.",
        font=("Arial", 11),
        bg=BG_COLOR,
        fg=MUTED_COLOR
    ).pack(anchor="w", padx=27)

    # --------------------------------------------------
    # STATISTICS CARDS
    # --------------------------------------------------

    cards_frame = tk.Frame(
        content,
        bg=BG_COLOR
    )

    cards_frame.pack(
        fill="x",
        padx=20,
        pady=18
    )

    def create_card(title, value, color, column):

        card = tk.Frame(
            cards_frame,
            bg=CARD_COLOR,
            padx=15,
            pady=15
        )

        card.grid(
            row=0,
            column=column,
            padx=7,
            sticky="nsew"
        )

        tk.Label(
            card,
            text=title,
            font=("Arial", 10),
            bg=CARD_COLOR,
            fg=MUTED_COLOR
        ).pack(anchor="w")

        tk.Label(
            card,
            text=value,
            font=("Arial", 22, "bold"),
            bg=CARD_COLOR,
            fg=color
        ).pack(anchor="w", pady=(10, 0))

    for i in range(4):
        cards_frame.columnconfigure(i, weight=1)

    create_card(
        "Total Members",
        total_members,
        TEXT_COLOR,
        0
    )

    create_card(
        "Active Members",
        active_members,
        GREEN,
        1
    )

    create_card(
        "Today's Revenue",
        f"₹{today_revenue:,.0f}",
        ORANGE,
        2
    )

    create_card(
        "Today's Attendance",
        today_attendance,
        ACCENT_COLOR,
        3
    )

    # --------------------------------------------------
    # CHART SECTION
    # --------------------------------------------------

    charts_frame = tk.Frame(
        content,
        bg=BG_COLOR
    )

    charts_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=5
    )

    chart_card = tk.Frame(
        charts_frame,
        bg=CARD_COLOR
    )

    chart_card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 10)
    )

    tk.Label(
        chart_card,
        text="Monthly Revenue",
        font=("Arial", 14, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", padx=15, pady=12)

    # Monthly revenue chart
    months = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ]

    revenue_values = [0] * 12

    for month_number, amount in monthly_records:
        revenue_values[month_number - 1] = amount

    figure = Figure(
        figsize=(6, 3),
        dpi=90,
        facecolor=CARD_COLOR
    )

    axis = figure.add_subplot(111)

    axis.set_facecolor(CARD_COLOR)

    axis.bar(
        months,
        revenue_values,
        color="#3B82F6"
    )

    axis.set_ylabel(
        "Revenue (₹)",
        color=TEXT_COLOR
    )

    axis.tick_params(
        colors=TEXT_COLOR
    )

    axis.set_title(
        str(today.year),
        color=TEXT_COLOR
    )

    axis.spines["bottom"].set_color(MUTED_COLOR)
    axis.spines["left"].set_color(MUTED_COLOR)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

    axis.grid(
        axis="y",
        alpha=0.2
    )

    figure.tight_layout()

    canvas = FigureCanvasTkAgg(
        figure,
        master=chart_card
    )

    canvas.draw()

    canvas.get_tk_widget().pack(
        fill="both",
        expand=True,
        padx=10,
        pady=5
    )

    # --------------------------------------------------
    # MEMBERSHIP OVERVIEW
    # --------------------------------------------------

    overview = tk.Frame(
        charts_frame,
        bg=CARD_COLOR,
        width=220
    )

    overview.pack(
        side="right",
        fill="both",
        padx=(10, 0)
    )

    overview.pack_propagate(False)

    tk.Label(
        overview,
        text="Membership Overview",
        font=("Arial", 13, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", padx=15, pady=15)

    def overview_item(title, value, color):

        frame = tk.Frame(
            overview,
            bg=CARD_COLOR
        )

        frame.pack(
            fill="x",
            padx=15,
            pady=12
        )

        tk.Label(
            frame,
            text=title,
            font=("Arial", 10),
            bg=CARD_COLOR,
            fg=MUTED_COLOR
        ).pack(anchor="w")

        tk.Label(
            frame,
            text=str(value),
            font=("Arial", 19, "bold"),
            bg=CARD_COLOR,
            fg=color
        ).pack(anchor="w")

    overview_item(
        "Active Memberships",
        active_members,
        GREEN
    )

    overview_item(
        "Expired Memberships",
        expired_members,
        RED
    )

    overview_item(
        "Total Members",
        total_members,
        TEXT_COLOR
    )

    # --------------------------------------------------
    # BOTTOM SECTION
    # --------------------------------------------------

    bottom_frame = tk.Frame(
        content,
        bg=BG_COLOR
    )

    bottom_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=15
    )

    # Recent payments
    payments_frame = tk.Frame(
        bottom_frame,
        bg=CARD_COLOR
    )

    payments_frame.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 10)
    )

    tk.Label(
        payments_frame,
        text="Recent Payments",
        font=("Arial", 13, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", padx=15, pady=12)

    columns = (
        "Member",
        "Amount",
        "Date",
        "Method"
    )

    payment_tree = ttk.Treeview(
        payments_frame,
        columns=columns,
        show="headings",
        height=4
    )

    for col in columns:
        payment_tree.heading(col, text=col)
        payment_tree.column(
            col,
            width=100,
            anchor="center"
        )

    payment_tree.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=5
    )

    for record in recent_payments:

        name, amount, payment_date, method = record

        payment_tree.insert(
            "",
            "end",
            values=(
                name,
                f"₹{amount:,.0f}",
                payment_date,
                method
            )
        )

    # Expiring memberships
    alerts_frame = tk.Frame(
        bottom_frame,
        bg=CARD_COLOR,
        width=230
    )

    alerts_frame.pack(
        side="right",
        fill="both",
        padx=(10, 0)
    )

    alerts_frame.pack_propagate(False)

    tk.Label(
        alerts_frame,
        text="Membership Alerts",
        font=("Arial", 13, "bold"),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", padx=12, pady=12)

    if expiring_members:

        for name, phone, expiry in expiring_members[:4]:

            tk.Label(
                alerts_frame,
                text=f"{name}\nExpires: {expiry}",
                font=("Arial", 9),
                bg=CARD_COLOR,
                fg=ORANGE,
                justify="left"
            ).pack(anchor="w", padx=12, pady=5)

    else:

        tk.Label(
            alerts_frame,
            text="No memberships expiring soon.",
            font=("Arial", 9),
            bg=CARD_COLOR,
            fg=GREEN,
            wraplength=190
        ).pack(anchor="w", padx=12, pady=10)

    # --------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------

    quick_frame = tk.Frame(
        content,
        bg=BG_COLOR
    )

    quick_frame.pack(
        fill="x",
        padx=25,
        pady=(0, 15)
    )

    tk.Label(
        quick_frame,
        text="Quick Actions",
        font=("Arial", 12, "bold"),
        bg=BG_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", pady=(0, 8))

    actions = [
        ("+ Add Member", lambda: show_add_member(content)),
        ("Attendance", lambda: show_attendance(content)),
        ("Record Payment", lambda: show_payments(content)),
        ("View Reports", lambda: show_reports(content))
    ]

    for title, command in actions:

        tk.Button(
            quick_frame,
            text=title,
            command=command,
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=15,
            pady=9,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

menu_items = [
    "Dashboard",
    "Add Member",
    "Manage Members",
    "Attendance",
    "Membership",
    "Payments",
    "Reports",
    "Settings"
]


def create_menu_button(name):

    if name == "Dashboard":
        action = show_dashboard

    elif name == "Add Member":
        action = lambda: show_add_member(content)

    elif name == "Manage Members":
        action = lambda: show_manage_members(content)

    elif name == "Attendance":
        action = lambda: show_attendance(content)

    elif name == "Membership":
        action = lambda: show_membership(content)

    elif name == "Payments":
        action = lambda: show_payments(content)

    elif name == "Reports":
        action = lambda: show_reports(content)

    else:
        action = lambda: print(name, "Coming Soon")

    button = tk.Button(
        sidebar,
        text=name,
        font=("Arial", 12),
        bg=SIDEBAR_COLOR,
        fg=TEXT_COLOR,
        activebackground=ACCENT_COLOR,
        activeforeground=TEXT_COLOR,
        relief="flat",
        anchor="w",
        padx=25,
        pady=12,
        cursor="hand2",
        command=action
    )

    button.pack(
        fill="x",
        padx=10,
        pady=3
    )


for item in menu_items:
    create_menu_button(item)


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

backup_database()

# Show dashboard immediately
show_dashboard()

root.mainloop()