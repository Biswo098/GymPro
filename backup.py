import sqlite3
import os
from datetime import datetime, date


def backup_database():

    database_path = "database/gym.db"
    backup_folder = "backups"

    # Check whether database exists
    if not os.path.exists(database_path):
        print("Database not found. Backup skipped.")
        return

    # Create backup folder if it doesn't exist
    os.makedirs(backup_folder, exist_ok=True)

    # Create one backup per day
    today = date.today().isoformat()

    backup_name = f"gym_backup_{today}.db"

    backup_path = os.path.join(
        backup_folder,
        backup_name
    )

    # Avoid duplicate daily backups
    if os.path.exists(backup_path):
        print("Today's backup already exists.")
        return

    try:

        source = sqlite3.connect(database_path)
        destination = sqlite3.connect(backup_path)

        source.backup(destination)

        destination.close()
        source.close()

        print("Database backup created successfully!")

        # Keep only the latest 30 backups
        backups = sorted([
            file for file in os.listdir(backup_folder)
            if file.startswith("gym_backup_")
            and file.endswith(".db")
        ])

        while len(backups) > 30:

            old_backup = backups.pop(0)

            os.remove(
                os.path.join(backup_folder, old_backup)
            )

        print("Backup management completed.")

    except Exception as error:

        print("Backup Error:", error)