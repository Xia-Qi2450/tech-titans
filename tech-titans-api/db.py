import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "tech_titans.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    conn.close()
