import sqlite3
import pytest

@pytest.fixture
def simple_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS events;
    CREATE TABLE events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        title TEXT NOT NULL,
        room TEXT,
        group_name TEXT NOT NULL
    );

    DROP TABLE IF EXISTS users;
    CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        notifications_enabled INTEGER NOT NULL DEFAULT 1,
        group_name TEXT
    );
    """)
    conn.commit()
    yield conn
    conn.close()
