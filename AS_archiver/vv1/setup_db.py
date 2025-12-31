import sqlite3

con = sqlite3.connect("archived_reports.db")

cursor = con.cursor()

cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports(
            patient_id TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            modality TEXT NOT NULL,
            date_report DATE NOT NULL,
            file_path UNIQUE
            )
            """)
print("\nThe database was created successfully!")

# cur.execute("""

#             """)

