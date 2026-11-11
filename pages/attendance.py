import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date


def show_attendance(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="#101827")

    # Heading
    tk.Label(
        parent,
        text="Attendance Management",
        font=("Arial", 24, "bold"),
        bg="#101827",
        fg="white"
    ).pack(anchor="w", padx=30, pady=20)

    # Database Connection
    conn = sqlite3.connect("database/gym.db")
    cursor = conn.cursor()

    # Main Frame
    main_frame = tk.Frame(parent, bg="#1E2D45")
    main_frame.pack(fill="both", expand=True, padx=30, pady=15)

    # Today's Date
    today = date.today().isoformat()

    tk.Label(
        main_frame,
        text=f"Date: {today}",
        font=("Arial", 13, "bold"),
        bg="#1E2D45",
        fg="white"
    ).pack(anchor="w", padx=20, pady=15)

    # Select Member
    tk.Label(
        main_frame,
        text="Select Gym Member",
        font=("Arial", 12),
        bg="#1E2D45",
        fg="white"
    ).pack(anchor="w", padx=20)

    member_combo = ttk.Combobox(
        main_frame,
        state="readonly",
        width=45,
        font=("Arial", 11)
    )

    member_combo.pack(anchor="w", padx=20, pady=10)

    # Load Active Members
    cursor.execute("""
        SELECT m.member_id, m.name, m.phone
        FROM members m
        JOIN memberships ms
        ON m.member_id = ms.member_id
        WHERE ms.end_date >= ?
        AND ms.membership_id = (
            SELECT MAX(ms2.membership_id)
            FROM memberships ms2
            WHERE ms2.member_id = m.member_id
        )
        ORDER BY m.name
    """, (today,))

    members = cursor.fetchall()

    member_data = {}

    for member in members:

        display_name = (
            f"{member[0]} - {member[1]} - {member[2]}"
        )

        member_data[display_name] = member[0]

    member_combo["values"] = list(member_data.keys())

    # Attendance Table
    tk.Label(
        main_frame,
        text="Today's Attendance",
        font=("Arial", 16, "bold"),
        bg="#1E2D45",
        fg="white"
    ).pack(anchor="w", padx=20, pady=(25, 10))

    columns = ("Member ID", "Name", "Phone", "Date", "Status")

    tree = ttk.Treeview(
        main_frame,
        columns=columns,
        show="headings",
        height=10
    )

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")

    tree.pack(fill="both", expand=True, padx=20, pady=10)

    # Table Styling
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

    # Load Today's Attendance
    def load_attendance():

        for row in tree.get_children():
            tree.delete(row)

        cursor.execute("""
            SELECT
                m.member_id,
                m.name,
                m.phone,
                a.attendance_date,
                a.status
            FROM attendance a
            JOIN members m
            ON a.member_id = m.member_id
            WHERE a.attendance_date = ?
            ORDER BY a.attendance_id DESC
        """, (today,))

        records = cursor.fetchall()

        for record in records:
            tree.insert("", "end", values=record)

        count_label.config(
            text=f"Total Present Today: {len(records)}"
        )

    # Mark Attendance
    def mark_attendance():

        selected = member_combo.get()

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Please select a member first."
            )
            return

        member_id = member_data[selected]

        try:

            cursor.execute("""
                INSERT INTO attendance
                (member_id, attendance_date, status)
                VALUES (?, ?, ?)
            """, (member_id, today, "Present"))

            conn.commit()

            messagebox.showinfo(
                "Success",
                "Attendance marked successfully!"
            )

            load_attendance()

        except sqlite3.IntegrityError:

            messagebox.showwarning(
                "Already Marked",
                "This member's attendance is already marked today."
            )

    # Buttons
    button_frame = tk.Frame(main_frame, bg="#1E2D45")
    button_frame.pack(pady=15)

    tk.Button(
        button_frame,
        text="MARK PRESENT",
        command=mark_attendance,
        bg="#2563EB",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=20,
        pady=10
    ).pack(side="left", padx=10)

    tk.Button(
        button_frame,
        text="REFRESH",
        command=load_attendance,
        bg="#334155",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=20,
        pady=10
    ).pack(side="left", padx=10)

    count_label = tk.Label(
        main_frame,
        text="Total Present Today: 0",
        font=("Arial", 12, "bold"),
        bg="#1E2D45",
        fg="#22C55E"
    )

    count_label.pack(pady=10)

    load_attendance()

    def close_connection():
        conn.close()

    # Close database connection when leaving page
    parent.bind("<Destroy>", lambda event: close_connection())

