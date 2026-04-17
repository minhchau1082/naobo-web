import sqlite3
import os

DB_PATH = "brain.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    for table_name in tables:
        print(f"\nSchema for {table_name[0]}:")
        cursor.execute(f"PRAGMA table_info({table_name[0]})")
        for col in cursor.fetchall():
            print(col)
            
        cursor.execute(f"SELECT * FROM {table_name[0]} LIMIT 5")
        rows = cursor.fetchall()
        print(f"Sample data for {table_name[0]}:", rows)
        
    conn.close()

if __name__ == "__main__":
    check_db()
