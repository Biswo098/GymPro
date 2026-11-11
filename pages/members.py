import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
import calendar


def add_months(start_date, months):
    month = start_date.month - 1 + months

    year = start_date.year + month // 12
    month = month % 12 + 1

    day = min(start_date.day, calendar.monthrange(year, month)[1])

    return date(year, month, day)


def show_add_member(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="#101827")

    tk.Label(
        parent,
        text="Register New Member",
        font=("Arial", 24, "bold"),
        bg="#101827",
        fg="white"
    ).pack(anchor="w", padx=30, pady=25)

    form = tk.Frame(parent, bg="#1E2D45")
    form.pack(fill="both", expand=True, padx=30, pady=10)

    fields = {}

    def create_field(label, row, column, default=""):

        tk.Label(
            form,
            text=label,
            font=("Arial", 11),
            bg="#1E2D45",
            fg="white"
        ).grid(row=row, column=column, padx=20, pady=12, sticky="w")

        entry = tk.Entry(
            form,
            font=("Arial", 12),
            width=25
        )

        entry.grid(
            row=row + 1,
            column=column,
            padx=20,
            pady=5,
            sticky="w"
        )

        entry.insert(0, default)

        fields[label] = entry

    # Member Information

    create_field("Full Name", 0, 0)
    create_field("Phone Number", 0, 1)
    create_field("Age", 2, 0)

    tk.Label(
        form,
        text="Gender",
        font=("Arial", 11),
        bg="#1E2D45",
        fg="white"
    ).grid(row=2, column=1, padx=20, pady=12, sticky="w")

    gender = ttk.Combobox(
        form,
        values=["Male", "Female", "Other"],
        state="readonly",
        width=23
    )

    gender.grid(row=3, column=1, padx=20, pady=5, sticky="w")
    gender.set("Male")

    # Membership Information

    create_field(
        "Joining Date (YYYY-MM-DD)",
        4, 0, date.today().isoformat()
    )

    tk.Label(
        form,
        text="Membership Plan",
        font=("Arial", 11),
        bg="#1E2D45",
        fg="white"
    ).grid(row=4, column=1, padx=20, pady=12, sticky="w")

    plan = ttk.Combobox(
        form,
        values=["1 Month", "3 Months", "6 Months", "12 Months"],
        state="readonly",
        width=23
    )

    plan.grid(row=5, column=1, padx=20, pady=5, sticky="w")
    plan.set("1 Month")

    create_field("Membership Amount (₹)", 6, 0)

    tk.Label(
        form,
        text="Payment Method",
        font=("Arial", 11),
        bg="#1E2D45",
        fg="white"
    ).grid(row=6, column=1, padx=20, pady=12, sticky="w")

    payment_method = ttk.Combobox(
        form,
        values=["Cash", "UPI", "Card", "Bank Transfer"],
        state="readonly",
        width=23
    )

    payment_method.grid(row=7, column=1, padx=20, pady=5, sticky="w")
    payment_method.set("Cash")

    # Save Member Function

    def save_member():

        name = fields["Full Name"].get().strip()
        phone = fields["Phone Number"].get().strip()
        age = fields["Age"].get().strip()
        joining = fields["Joining Date (YYYY-MM-DD)"].get().strip()
        amount = fields["Membership Amount (₹)"].get().strip()

        if not name or not phone or not amount:
            messagebox.showerror(
                "Error",
                "Please fill all required fields."
            )
            return

        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror(
                "Error",
                "Enter a valid 10-digit phone number."
            )
            return

        try:
            age_value = int(age) if age else None

            if age_value is not None and not 1 <= age_value <= 120:
                raise ValueError

            amount_value = float(amount)

            if amount_value <= 0:
                raise ValueError

            start_date = date.fromisoformat(joining)

            if start_date > date.today():
                messagebox.showerror(
                    "Error",
                    "Joining date cannot be in the future."
                )
                return

        except ValueError:
            messagebox.showerror(
                "Error",
                "Check age, amount and joining date."
            )
            return

        plan_name = plan.get()

        months = {
            "1 Month": 1,
            "3 Months": 3,
            "6 Months": 6,
            "12 Months": 12
        }

        end_date = add_months(
            start_date,
            months[plan_name]
        )

        try:

            conn = sqlite3.connect("database/gym.db")
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO members
                (name, phone, age, gender, joining_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                phone,
                age_value,
                gender.get(),
                start_date.isoformat()
            ))

            member_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO memberships
                (member_id, plan, amount, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                member_id,
                plan_name,
                amount_value,
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
                amount_value,
                date.today().isoformat(),
                payment_method.get()
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success",
                f"Member registered successfully!\n\n"
                f"Member ID: {member_id}\n"
                f"Expiry Date: {end_date}"
            )

            show_add_member(parent)

        except sqlite3.IntegrityError:
            if 'conn' in locals():
                conn.rollback()
                conn.close()

            messagebox.showerror(
                "Error",
                "This phone number is already registered."
            )

        except sqlite3.Error as error:
            if 'conn' in locals():
                conn.rollback()
                conn.close()

            messagebox.showerror(
                "Database Error",
                str(error)
            )

    # Register Button

    tk.Button(
        form,
        text="REGISTER MEMBER",
        font=("Arial", 12, "bold"),
        bg="#2563EB",
        fg="white",
        activebackground="#1D4ED8",
        cursor="hand2",
        relief="flat",
        padx=25,
        pady=12,
        command=save_member
    ).grid(
        row=9,
        column=0,
        columnspan=2,
        pady=35
    )