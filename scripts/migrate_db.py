import sqlite3
import os
from pathlib import Path

def migrate():
    # Determine the database path
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "app" / "backend" / "hedge_fund.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define the columns to add and their types/defaults
    # Format: (column_name, sql_definition)
    columns_to_add = [
        ("validation_status", "VARCHAR(20) DEFAULT 'valid'"),
        ("validation_error", "TEXT"),
        ("last_validated_at", "DATETIME"),
        ("last_validation_latency_ms", "INTEGER"),
        ("description", "TEXT"),
        ("last_used", "DATETIME")
    ]

    # Get existing columns
    cursor.execute("PRAGMA table_info(api_keys)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    added_count = 0
    for col_name, col_def in columns_to_add:
        if col_name not in existing_columns:
            print(f"Adding column '{col_name}' to table 'api_keys'...")
            try:
                cursor.execute(f"ALTER TABLE api_keys ADD COLUMN {col_name} {col_def}")
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"Error adding column '{col_name}': {e}")
        else:
            print(f"Column '{col_name}' already exists.")

    conn.commit()
    conn.close()

    if added_count > 0:
        print(f"Migration successful. Added {added_count} columns.")
    else:
        print("No migration needed. All columns already exist.")

if __name__ == "__main__":
    migrate()
