import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
DB_PATH = DATA_DIR / "aptitude.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    schema_path = BASE_DIR / "backend" / "models" / "schema.sql"
    with sqlite3.connect(DB_PATH) as conn:
        with open(schema_path, "r") as f:
            conn.executescript(f.read())

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
