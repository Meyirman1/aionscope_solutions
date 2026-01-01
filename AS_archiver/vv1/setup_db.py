import sqlite3

db_name = "archived_reports.db"

def create_table():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        modality TEXT NOT NULL,
        report_date TEXT NOT NULL,
        file_path TEXT UNIQUE
        )
        """)

    conn.commit()
    conn.close()
    print(f"\nThe {db_name} database was created successfully!")

# if __name__ == '__archiver__':
create_table()

# cur.execute("""

#             """)

