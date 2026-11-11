import sqlite3
import os

# Create database folder if it doesn't exist
os.makedirs("database", exist_ok=True)

# Connect to SQLite database
conn = sqlite3.connect("database/gym.db")

# Create cursor
cursor = conn.cursor()


# 1. Members Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    age INTEGER,
    gender TEXT,
    joining_date TEXT NOT NULL
)
""")


# 2. Memberships Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS memberships (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    plan TEXT NOT NULL,
    amount REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    FOREIGN KEY (member_id) REFERENCES members(member_id)
)
""")


# 3. Attendance Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT DEFAULT 'Present',
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    UNIQUE(member_id, attendance_date)
)
""")


# 4. Payments Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    payment_method TEXT,
    FOREIGN KEY (member_id) REFERENCES members(member_id)
)
""")


# Save changes
conn.commit()

# Close connection
conn.close()

print("GymPro database created successfully!")

