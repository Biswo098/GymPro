import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date


def show_manage_members(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="#101827")

    # Heading
    tk.Label(
        parent,
        text="Manage Members",
        font=("Arial", 24, "bold"),
        bg="#101827",
        fg="white"
    ).pack(anchor="w", padx=30, pady=20)

    # Search Section
    search_frame = tk.Frame(parent, bg="#101827")
    search_frame.pack(fill="x", padx=30, pady=10)

    search_entry = tk.Entry(
        search_frame,
        font=("Arial", 12),
        width=35
    )
    search_entry.pack(side="left", padx=5)

    # Table Frame
    table_frame = tk.Frame(parent, bg="#1E2D45")
    table_frame.pack(fill="both", expand=True, padx=30, pady=20)

    columns = (
        "ID",
        "Name",
        "Phone",
        "Plan",
        "Amount",
        "Start Date",
        "End Date",
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

    # Table Styling
    style = ttk.Style()
    style.theme_use("clam")

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

    # Load Members
    def load_members(keyword=""):

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
                ms.end_date,
                ms.status
            FROM members m
            LEFT JOIN memberships ms
            ON m.member_id = ms.member_id
            WHERE m.name LIKE ? OR m.phone LIKE ?
            ORDER BY m.member_id DESC
        """, (
            f"%{keyword}%",
            f"%{keyword}%"
        ))

        records = cursor.fetchall()
        conn.close()

        today = date.today().isoformat()

        for record in records:

            status = "Expired" if record[6] and record[6] < today else "Active"

            tree.insert(
                "",
                "end",
                values=(
                    record[0],
                    record[1],
                    record[2],
                    record[3],
                    f"₹{record[4]:.2f}" if record[4] is not None else "-",
                    record[5],
                    record[6],
                    status
                )
            )

    # Search Function
    def search_members():
        load_members(search_entry.get().strip())

    tk.Button(
        search_frame,
        text="Search",
        command=search_members,
        bg="#2563EB",
        fg="white",
        font=("Arial", 11),
        padx=15
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame,
        text="Refresh",
        command=lambda: load_members(),
        bg="#334155",
        fg="white",
        font=("Arial", 11),
        padx=15
    ).pack(side="left", padx=5)

    load_members()

