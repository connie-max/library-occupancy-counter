"""database.py - saves and reads seat readings using SQLite.

Table: readings(id, timestamp, seat, taken)
  timestamp = text like "2026-10-21 15:30:00"
  seat      = text like "T1-S1"
  taken     = 1 if taken, 0 if vacant

No camera images are ever saved. Only these three values.
"""

import os
import sqlite3
from datetime import datetime

# the database file (the data/ folder is ignored by Git)
DB_PATH = os.environ.get("SEAT_DB_PATH", os.path.join("data", "seats.db"))


def _connect(path=None):
    """Open the database. Make the data folder if it does not exist."""
    path = path or DB_PATH
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    return sqlite3.connect(path)


def init_db(path=None):
    """Make the readings table if it does not exist yet."""
    conn = _connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS readings (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               timestamp TEXT NOT NULL,
               seat TEXT NOT NULL,
               taken INTEGER NOT NULL
           )"""
    )
    conn.commit()
    conn.close()


def save_reading(status, path=None):
    """Save one check of every seat.

    status = {"T1-S1": True, "T1-S2": False, ...}
    All seats in one check share the same timestamp.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [(now, seat, 1 if is_taken else 0) for seat, is_taken in status.items()]
    conn = _connect(path)
    conn.executemany(
        "INSERT INTO readings (timestamp, seat, taken) VALUES (?, ?, ?)", rows
    )
    conn.commit()
    conn.close()


def get_latest(path=None):
    """Return the newest check as {"T1-S1": True, ...}. Empty dict if no data."""
    conn = _connect(path)
    newest = conn.execute("SELECT MAX(timestamp) FROM readings").fetchone()[0]
    if newest is None:
        conn.close()
        return {}
    rows = conn.execute(
        "SELECT seat, taken FROM readings WHERE timestamp = ?", (newest,)
    ).fetchall()
    conn.close()
    return {seat: bool(taken) for seat, taken in rows}


def get_history(path=None):
    """Return every reading as a list of (timestamp, seat, taken), oldest first."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT timestamp, seat, taken FROM readings ORDER BY timestamp, seat"
    ).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    # quick self-test using a temporary file, so it never touches real data
    test_path = os.path.join("data", "test_seats.db")
    if os.path.exists(test_path):
        os.remove(test_path)

    init_db(test_path)
    print(get_latest(test_path))  # {} because nothing is saved yet

    save_reading({"T1-S1": True, "T1-S2": False}, test_path)
    print(get_latest(test_path))  # {'T1-S1': True, 'T1-S2': False}
    print(get_history(test_path))  # 2 rows

    os.remove(test_path)