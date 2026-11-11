import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date


def show_payments(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    # Heading
    tk.Label(
        parent,
        text="Payments Management",
        font=("Segoe UI", 22, "bold"),
        bg="#F4F7FB",
        fg="#172B4D"
    ).pack(anchor="w", padx=25, pady=(20, 5))

    tk.Label(
        parent,
        text="Manage gym payments and track revenue.",
        font=("Segoe UI", 10),
        bg="#F4F7FB",
        fg="#64748B"
    ).pack(anchor="w", padx=25)

    # Database connection
    def get_connection():
        return sqlite3.connect("database/gym.db")

    # Revenue summary
    summary_frame = tk.Frame(parent, bg="#F4F7FB")
    summary_frame.pack(fill="x", padx=25, pady=20)

    def create_card(title, value, column):

        card = tk.Frame(
            summary_frame,
            bg="white",
            padx=25,
            pady=18
        )

        card.grid(row=0, column=column, padx=(0, 15), sticky="ew")

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10),
            bg="white",
            fg="#64748B"
        ).pack(anchor="w")

        label = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#172B4D"
        )

        label.pack(anchor="w", pady=(5, 0))

        return label

    summary_frame.columnconfigure((0, 1), weight=1)

    total_label = create_card("Total Collection", "₹0", 0)
    today_label = create_card("Today's Collection", "₹0", 1)

    # Search and buttons
    control_frame = tk.Frame(parent, bg="#F4F7FB")
    control_frame.pack(fill="x", padx=25, pady=5)

    search_var = tk.StringVar()

    search_entry = tk.Entry(
        control_frame,
        textvariable=search_var,
        font=("Segoe UI", 11),
        width=30
    )

    search_entry.pack(side="left", ipady=7)

    # Payment table
    table_frame = tk.Frame(parent, bg="white")
    table_frame.pack(fill="both", expand=True, padx=25, pady=15)

    columns = (
        "ID",
        "Member",
        "Phone",
        "Amount",
        "Payment Date",
        "Payment Method"
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    for col in columns:

        tree.heading(col, text=col)

        tree.column(
            col,
            width=130,
            anchor="center"
        )

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Load payment records
    def load_payments():

        tree.delete(*tree.get_children())

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                payments.payment_id,
                members.name,
                members.phone,
                payments.amount,
                payments.payment_date,
                payments.payment_method
            FROM payments
            JOIN members
            ON payments.member_id = members.member_id
            ORDER BY payments.payment_id DESC
        """)

        records = cursor.fetchall()

        total = 0
        today_total = 0

        today = date.today().isoformat()
        search_text = search_var.get().lower()

        for record in records:

            payment_id, name, phone, amount, payment_date, method = record

            total += amount

            if payment_date == today:
                today_total += amount

            if (
                search_text in str(name).lower()
                or search_text in str(phone).lower()
            ):

                tree.insert(
                    "",
                    "end",
                    values=(
                        payment_id,
                        name,
                        phone,
                        f"₹{amount:.2f}",
                        payment_date,
                        method
                    )
                )

        total_label.config(text=f"₹{total:.2f}")
        today_label.config(text=f"₹{today_total:.2f}")

        conn.close()

    # Add new payment
    def add_payment():

        window = tk.Toplevel(parent)
        window.title("Record Payment")
        window.geometry("400x450")
        window.configure(bg="white")
        window.resizable(False, False)

        tk.Label(
            window,
            text="Record New Payment",
            font=("Segoe UI", 18, "bold"),
            bg="white",
            fg="#172B4D"
        ).pack(pady=20)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT member_id, name, phone
            FROM members
            ORDER BY name
        """)

        members = cursor.fetchall()
        conn.close()

        if not members:
            messagebox.showwarning(
                "No Members",
                "Please register a member first.",
                parent=window
            )
            window.destroy()
            return

        tk.Label(
            window,
            text="Select Member",
            bg="white"
        ).pack(anchor="w", padx=35)

        member_var = tk.StringVar()

        member_box = ttk.Combobox(
            window,
            textvariable=member_var,
            state="readonly",
            width=35
        )

        member_box["values"] = [
            f"{m[0]} - {m[1]} ({m[2]})"
            for m in members
        ]

        member_box.pack(pady=7)

        member_box.current(0)

        tk.Label(
            window,
            text="Payment Amount",
            bg="white"
        ).pack(anchor="w", padx=35, pady=(10, 0))

        amount_entry = tk.Entry(window, width=38)
        amount_entry.pack(pady=7, ipady=5)

        tk.Label(
            window,
            text="Payment Method",
            bg="white"
        ).pack(anchor="w", padx=35, pady=(10, 0))

        method_box = ttk.Combobox(
            window,
            values=["Cash", "UPI", "Card", "Bank Transfer"],
            state="readonly",
            width=35
        )

        method_box.pack(pady=7)
        method_box.current(0)

        tk.Label(
            window,
            text="Payment Date (YYYY-MM-DD)",
            bg="white"
        ).pack(anchor="w", padx=35, pady=(10, 0))

        date_entry = tk.Entry(window, width=38)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(pady=7, ipady=5)

        def save_payment():

            try:
                member_id = int(member_var.get().split(" - ")[0])
                amount = float(amount_entry.get())
                payment_date = date.fromisoformat(
                    date_entry.get().strip()
                )

                if amount <= 0:
                    messagebox.showerror(
                        "Invalid Amount",
                        "Amount must be greater than zero.",
                        parent=window
                    )
                    return

                method = method_box.get()

                if not method:
                    messagebox.showerror(
                        "Missing Method",
                        "Please select a payment method.",
                        parent=window
                    )
                    return

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO payments
                    (member_id, amount, payment_date, payment_method)
                    VALUES (?, ?, ?, ?)
                """, (
                    member_id,
                    amount,
                    payment_date.isoformat(),
                    method
                ))

                conn.commit()
                conn.close()

                messagebox.showinfo(
                    "Success",
                    "Payment recorded successfully!",
                    parent=window
                )

                window.destroy()
                load_payments()

            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Please enter a valid amount and date.",
                    parent=window
                )

        tk.Button(
            window,
            text="Save Payment",
            command=save_payment,
            bg="#2563EB",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=20,
            pady=10
        ).pack(pady=20)

    # Buttons
    tk.Button(
        control_frame,
        text="Search",
        command=load_payments,
        bg="#2563EB",
        fg="white",
        relief="flat",
        padx=15,
        pady=7
    ).pack(side="left", padx=10)

    tk.Button(
        control_frame,
        text="Add Payment +",
        command=add_payment,
        bg="#16A34A",
        fg="white",
        relief="flat",
        padx=15,
        pady=7
    ).pack(side="right")

    search_entry.bind(
        "<Return>",
        lambda event: load_payments()
    )

    load_payments()