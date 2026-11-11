import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, timedelta
import calendar


def add_months(start_date, months):

    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1

    day = min(
        start_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def show_membership(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="#101827")

    today = date.today()

    tk.Label(
        parent,
        text="Membership Management",
        font=("Arial", 24, "bold"),
        bg="#101827",
        fg="white"
    ).pack(anchor="w", padx=30, pady=20)

    # Statistics
    stats_frame = tk.Frame(parent, bg="#101827")
    stats_frame.pack(fill="x", padx=20)

    # Search
    search_frame = tk.Frame(parent, bg="#101827")
    search_frame.pack(fill="x", padx=30, pady=15)

    search_entry = tk.Entry(
        search_frame,
        font=("Arial", 12),
        width=30
    )
    search_entry.pack(side="left", padx=5)

    # Table
    table_frame = tk.Frame(parent, bg="#1E2D45")
    table_frame.pack(fill="both", expand=True, padx=30, pady=15)

    columns = (
        "ID",
        "Name",
        "Phone",
        "Plan",
        "Amount",
        "Start Date",
        "Expiry Date",
        "Status"
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110, anchor="center")

    tree.pack(fill="both", expand=True)

    style = ttk.Style()

    style.configure(
        "Treeview",
        background="#1E2D45",
        foreground="white",
        fieldbackground="#1E2D45",
        rowheight=30
    )

    style.configure(
        "Treeview.Heading",
        background="#2563EB",
        foreground="white",
        font=("Arial", 10, "bold")
    )

    # Load Memberships
    def load_memberships(keyword=""):

        for row in tree.get_children():
            tree.delete(row)

        conn = sqlite3.connect("database/gym.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.member_id,
                m.name,
                m.phone,
                ms.plan,
                ms.amount,
                ms.start_date,
                ms.end_date
            FROM members m
            JOIN memberships ms
            ON m.member_id = ms.member_id
            WHERE ms.membership_id = (
                SELECT MAX(ms2.membership_id)
                FROM memberships ms2
                WHERE ms2.member_id = m.member_id
            )
            AND (m.name LIKE ? OR m.phone LIKE ?)
            ORDER BY m.member_id DESC
        """, (
            f"%{keyword}%",
            f"%{keyword}%"
        ))

        records = cursor.fetchall()
        conn.close()

        active = 0
        expired = 0
        expiring = 0

        for record in records:

            expiry = date.fromisoformat(record[6])

            if expiry < today:
                status = "Expired"
                expired += 1

            elif expiry <= today + timedelta(days=7):
                status = "Expiring Soon"
                active += 1
                expiring += 1

            else:
                status = "Active"
                active += 1

            tree.insert(
                "",
                "end",
                values=(
                    record[0],
                    record[1],
                    record[2],
                    record[3],
                    f"₹{record[4]:.2f}",
                    record[5],
                    record[6],
                    status
                )
            )

        active_label.config(text=f"Active: {active}")
        expired_label.config(text=f"Expired: {expired}")
        expiring_label.config(text=f"Expiring Soon: {expiring}")

    # Statistics Labels
    active_label = tk.Label(
        stats_frame,
        text="Active: 0",
        font=("Arial", 13, "bold"),
        bg="#1E2D45",
        fg="#22C55E",
        padx=20,
        pady=15
    )

    active_label.pack(side="left", padx=10)

    expired_label = tk.Label(
        stats_frame,
        text="Expired: 0",
        font=("Arial", 13, "bold"),
        bg="#1E2D45",
        fg="#EF4444",
        padx=20,
        pady=15
    )

    expired_label.pack(side="left", padx=10)

    expiring_label = tk.Label(
        stats_frame,
        text="Expiring Soon: 0",
        font=("Arial", 13, "bold"),
        bg="#1E2D45",
        fg="#F59E0B",
        padx=20,
        pady=15
    )

    expiring_label.pack(side="left", padx=10)

    # Search Button
    tk.Button(
        search_frame,
        text="Search",
        command=lambda: load_memberships(
            search_entry.get().strip()
        ),
        bg="#2563EB",
        fg="white",
        padx=15
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame,
        text="Refresh",
        command=lambda: load_memberships(),
        bg="#334155",
        fg="white",
        padx=15
    ).pack(side="left", padx=5)

    # Renew Membership
    def renew_membership():

        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Please select a member first."
            )
            return

        values = tree.item(selected[0], "values")

        member_id = values[0]
        member_name = values[1]

        window = tk.Toplevel(parent)
        window.title("Renew Membership")
        window.geometry("350x350")
        window.configure(bg="#1E2D45")
        window.transient(parent)
        window.grab_set()

        tk.Label(
            window,
            text=f"Renew: {member_name}",
            font=("Arial", 15, "bold"),
            bg="#1E2D45",
            fg="white"
        ).pack(pady=20)

        tk.Label(
            window,
            text="Select Plan",
            bg="#1E2D45",
            fg="white"
        ).pack()

        plan_box = ttk.Combobox(
            window,
            values=[
                "1 Month",
                "3 Months",
                "6 Months",
                "12 Months"
            ],
            state="readonly"
        )

        plan_box.pack(pady=8)
        plan_box.set("1 Month")

        tk.Label(
            window,
            text="Membership Amount (₹)",
            bg="#1E2D45",
            fg="white"
        ).pack(pady=5)

        amount_entry = tk.Entry(window)
        amount_entry.pack(pady=5)

        tk.Label(
            window,
            text="Payment Method",
            bg="#1E2D45",
            fg="white"
        ).pack(pady=5)

        method_box = ttk.Combobox(
            window,
            values=["Cash", "UPI", "Card", "Bank Transfer"],
            state="readonly"
        )

        method_box.pack(pady=5)
        method_box.set("Cash")

        def save_renewal():

            try:

                amount = float(amount_entry.get())

                if amount <= 0:
                    raise ValueError

                plan = plan_box.get()

                if not plan:
                    raise ValueError

                months = {
                    "1 Month": 1,
                    "3 Months": 3,
                    "6 Months": 6,
                    "12 Months": 12
                }

                conn = sqlite3.connect("database/gym.db")
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT end_date
                    FROM memberships
                    WHERE member_id = ?
                    ORDER BY membership_id DESC
                    LIMIT 1
                """, (member_id,))

                previous = cursor.fetchone()

                start_date = today

                if previous:
                    previous_end = date.fromisoformat(previous[0])

                    if previous_end >= today:
                        start_date = previous_end + timedelta(days=1)

                end_date = add_months(
                    start_date,
                    months[plan]
                )

                cursor.execute("""
                    INSERT INTO memberships
                    (member_id, plan, amount, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    member_id,
                    plan,
                    amount,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    "Active"
                ))

                cursor.execute("""
                    INSERT INTO payments
                    (member_id, amount, payment_date, payment_method)
                    VALUES (?, ?, ?, ?)
                """, (
                    member_id,
                    amount,
                    today.isoformat(),
                    method_box.get()
                ))

                conn.commit()
                conn.close()

                messagebox.showinfo(
                    "Success",
                    f"Membership renewed successfully!\n\n"
                    f"Member: {member_name}\n"
                    f"Start Date: {start_date}\n"
                    f"Expiry Date: {end_date}"
                )

                window.destroy()
                load_memberships()

            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Please enter a valid amount and plan."
                )

        tk.Button(
            window,
            text="RENEW MEMBERSHIP",
            command=save_renewal,
            bg="#2563EB",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=10
        ).pack(pady=20)

    tk.Button(
        search_frame,
        text="Renew Membership",
        command=renew_membership,
        bg="#16A34A",
        fg="white",
        padx=15
    ).pack(side="left", padx=5)

    load_memberships()