import sqlite3

db_name = "archived_reports.db"

def create_table():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports(
        report_order INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        filter_type TEXT NOT NULL,
        report_name TEXT NOT NULL,
        report_date TEXT NOT NULL,
        modality TEXT NOT NULL,
        file_path TEXT UNIQUE,
        archived_at TEXT NOT NULL
        )
        """)
         # 25/03/2026, 14:30:05     (d/m/y, time)
      # archived_timestamp TEXT NOT NULL
      # archived_time TEXT NOT NULL
      # archived_at TEXT NOT NULL  
    conn.commit()
    conn.close()
    print(f"\nThe {db_name} database was created successfully!")

create_table()


