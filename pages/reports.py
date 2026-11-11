import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd

from datetime import date, timedelta
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def show_reports(parent):

    for widget in parent.winfo_children():
        widget.destroy()

    # Main heading
    tk.Label(
        parent,
        text="Reports & Analytics",
        font=("Segoe UI", 22, "bold"),
        bg="#F4F7FB",
        fg="#172B4D"
    ).pack(anchor="w", padx=25, pady=(20, 5))

    tk.Label(
        parent,
        text="Analyze gym performance, revenue and attendance.",
        font=("Segoe UI", 10),
        bg="#F4F7FB",
        fg="#64748B"
    ).pack(anchor="w", padx=25)

    def get_connection():
        return sqlite3.connect("database/gym.db")

    # Latest membership for each member
    latest_membership = """
        SELECT m.member_id, m.name, m.phone,
               ms.plan, ms.amount, ms.start_date, ms.end_date
        FROM members m
        JOIN memberships ms
        ON ms.membership_id = (
            SELECT MAX(ms2.membership_id)
            FROM memberships ms2
            WHERE ms2.member_id = m.member_id
        )
    """

    today = date.today()
    today_string = today.isoformat()
    seven_days = (today + timedelta(days=7)).isoformat()

    # Statistics
    stats_frame = tk.Frame(parent, bg="#F4F7FB")
    stats_frame.pack(fill="x", padx=25, pady=20)

    def create_card(title, column):

        card = tk.Frame(
            stats_frame,
            bg="white",
            padx=20,
            pady=15
        )

        card.grid(row=0, column=column, padx=(0, 12), sticky="ew")

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10),
            bg="white",
            fg="#64748B"
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text="0",
            font=("Segoe UI", 19, "bold"),
            bg="white",
            fg="#172B4D"
        )

        value_label.pack(anchor="w", pady=(5, 0))

        return value_label

    for i in range(4):
        stats_frame.columnconfigure(i, weight=1)

    total_members_label = create_card("Total Members", 0)
    active_label = create_card("Active Members", 1)
    expired_label = create_card("Expired Members", 2)
    revenue_label = create_card("Total Revenue", 3)

    # Main chart area
    chart_frame = tk.Frame(parent, bg="white")
    chart_frame.pack(fill="both", expand=True, padx=25, pady=10)

    # Revenue chart
    def load_reports():

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Total members
            cursor.execute("SELECT COUNT(*) FROM members")
            total_members = cursor.fetchone()[0]

            # Latest membership statistics
            cursor.execute(f"""
                SELECT
                    COUNT(CASE
                        WHEN end_date >= ?
                        AND start_date <= ?
                        THEN 1 END),

                    COUNT(CASE
                        WHEN end_date < ?
                        THEN 1 END)
                FROM ({latest_membership})
            """, (
                today_string,
                today_string,
                today_string
            ))

            active_members, expired_members = cursor.fetchone()

            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
            """)

            total_revenue = cursor.fetchone()[0]

            total_members_label.config(text=str(total_members))
            active_label.config(text=str(active_members))
            expired_label.config(text=str(expired_members))
            revenue_label.config(text=f"₹{total_revenue:.2f}")

            # Monthly revenue for current year
            cursor.execute("""
                SELECT
                    CAST(strftime('%m', payment_date) AS INTEGER),
                    SUM(amount)
                FROM payments
                WHERE strftime('%Y', payment_date) = ?
                GROUP BY strftime('%m', payment_date)
                ORDER BY strftime('%m', payment_date)
            """, (str(today.year),))

            revenue_records = cursor.fetchall()

            # Daily attendance for last 7 days
            start_date = (today - timedelta(days=6)).isoformat()

            cursor.execute("""
                SELECT attendance_date, COUNT(*)
                FROM attendance
                WHERE attendance_date BETWEEN ? AND ?
                GROUP BY attendance_date
                ORDER BY attendance_date
            """, (start_date, today_string))

            attendance_records = cursor.fetchall()

            # Expiring memberships
            cursor.execute(f"""
                SELECT name, phone, plan, end_date
                FROM ({latest_membership})
                WHERE end_date BETWEEN ? AND ?
                ORDER BY end_date
            """, (today_string, seven_days))

            expiring_records = cursor.fetchall()

        finally:
            conn.close()

        # Clear previous chart
        for widget in chart_frame.winfo_children():
            widget.destroy()

        # Prepare revenue data
        months = [
            "Jan", "Feb", "Mar", "Apr",
            "May", "Jun", "Jul", "Aug",
            "Sep", "Oct", "Nov", "Dec"
        ]

        revenue_values = [0] * 12

        for month_number, amount in revenue_records:
            revenue_values[month_number - 1] = amount

        # Prepare attendance data
        attendance_dates = {
            record[0]: record[1]
            for record in attendance_records
        }

        last_seven_dates = [
            (today - timedelta(days=i)).isoformat()
            for i in range(6, -1, -1)
        ]

        attendance_values = [
            attendance_dates.get(day, 0)
            for day in last_seven_dates
        ]

        # Matplotlib figure
        figure = Figure(figsize=(9, 5), dpi=100)

        revenue_axis = figure.add_subplot(211)

        revenue_axis.bar(months, revenue_values)

        revenue_axis.set_title(
            f"Monthly Revenue - {today.year}"
        )

        revenue_axis.set_ylabel("Revenue (₹)")
        revenue_axis.grid(axis="y", alpha=0.3)

        attendance_axis = figure.add_subplot(212)

        attendance_axis.plot(
            [day[5:] for day in last_seven_dates],
            attendance_values,
            marker="o"
        )

        attendance_axis.set_title("Daily Attendance - Last 7 Days")
        attendance_axis.set_ylabel("Members Present")
        attendance_axis.set_xlabel("Date")
        attendance_axis.grid(alpha=0.3)

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(
            figure,
            master=chart_frame
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # Expiring membership section
        expiring_frame = tk.Frame(parent, bg="white")
        expiring_frame.pack(fill="x", padx=25, pady=(5, 15))

        tk.Label(
            expiring_frame,
            text="Memberships Expiring Within 7 Days",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg="#172B4D"
        ).pack(anchor="w", padx=12, pady=10)

        columns = ("Name", "Phone", "Plan", "Expiry Date")

        expiring_tree = ttk.Treeview(
            expiring_frame,
            columns=columns,
            show="headings",
            height=4
        )

        for col in columns:
            expiring_tree.heading(col, text=col)
            expiring_tree.column(col, width=150, anchor="center")

        expiring_tree.pack(fill="x", padx=10, pady=5)

        for record in expiring_records:
            expiring_tree.insert("", "end", values=record)

    # Export reports to Excel
    def export_excel():

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="GymPro_Report.xlsx"
        )

        if not file_path:
            return

        conn = get_connection()

        try:
            summary = pd.read_sql_query(f"""
                SELECT
                    COUNT(*) AS Total_Members,
                    SUM(CASE
                        WHEN end_date >= '{today_string}'
                        AND start_date <= '{today_string}'
                        THEN 1 ELSE 0 END) AS Active_Members,
                    SUM(CASE
                        WHEN end_date < '{today_string}'
                        THEN 1 ELSE 0 END) AS Expired_Members
                FROM ({latest_membership})
            """, conn)

            payments = pd.read_sql_query("""
                SELECT
                    p.payment_id,
                    m.name AS Member_Name,
                    m.phone AS Phone,
                    p.amount AS Amount,
                    p.payment_date AS Payment_Date,
                    p.payment_method AS Payment_Method
                FROM payments p
                JOIN members m
                ON p.member_id = m.member_id
                ORDER BY p.payment_date DESC
            """, conn)

            attendance = pd.read_sql_query("""
                SELECT
                    a.attendance_id,
                    m.name AS Member_Name,
                    m.phone AS Phone,
                    a.attendance_date AS Attendance_Date,
                    a.status AS Status
                FROM attendance a
                JOIN members m
                ON a.member_id = m.member_id
                ORDER BY a.attendance_date DESC
            """, conn)

            members = pd.read_sql_query(f"""
                SELECT * FROM ({latest_membership})
            """, conn)

            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:

                summary.to_excel(
                    writer,
                    sheet_name="Summary",
                    index=False
                )

                payments.to_excel(
                    writer,
                    sheet_name="Payments",
                    index=False
                )

                attendance.to_excel(
                    writer,
                    sheet_name="Attendance",
                    index=False
                )

                members.to_excel(
                    writer,
                    sheet_name="Members",
                    index=False
                )

            messagebox.showinfo(
                "Export Successful",
                "GymPro report exported successfully!"
            )

        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )

        finally:
            conn.close()

    # Bottom buttons
    button_frame = tk.Frame(parent, bg="#F4F7FB")
    button_frame.pack(fill="x", padx=25, pady=10)

    tk.Button(
        button_frame,
        text="Refresh Reports",
        command=load_reports,
        bg="#2563EB",
        fg="white",
        relief="flat",
        padx=15,
        pady=9
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Export to Excel",
        command=export_excel,
        bg="#16A34A",
        fg="white",
        relief="flat",
        padx=15,
        pady=9
    ).pack(side="right")

    load_reports()