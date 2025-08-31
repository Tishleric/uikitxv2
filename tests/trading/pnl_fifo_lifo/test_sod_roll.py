import os
import sqlite3
from datetime import datetime

from lib.trading.pnl_fifo_lifo.sod_roll import get_latest_close_date, roll_latest_close_to_sodtod


def _init_db(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS pricing")
    cur.execute(
        """
        CREATE TABLE pricing (
            symbol TEXT,
            price_type TEXT,
            price REAL,
            timestamp TEXT,
            PRIMARY KEY (symbol, price_type)
        )
        """
    )
    conn.commit()


def test_roll_latest_close_to_sodtod_single_day(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        _init_db(conn)
        cur = conn.cursor()

        # Insert closes for a date
        d = "2025-08-14"
        data = [
            ("TYU5 Comdty", "close", 111.59375, f"{d} 16:00:00"),
            ("USU5 Comdty", "close", 114.0, f"{d} 16:00:00"),
        ]
        cur.executemany(
            "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, ?, ?, ?)",
            data,
        )
        conn.commit()

        latest = get_latest_close_date(conn)
        assert latest.strftime('%Y-%m-%d') == d

        rolled_date, count = roll_latest_close_to_sodtod(conn)
        assert rolled_date.strftime('%Y-%m-%d') == d
        assert count == 2

        rows = cur.execute("SELECT symbol, price, timestamp FROM pricing WHERE price_type='sodTod' ORDER BY symbol").fetchall()
        assert rows == [
            ("TYU5 Comdty", 111.59375, f"{d} 06:00:00"),
            ("USU5 Comdty", 114.0, f"{d} 06:00:00"),
        ]
    finally:
        conn.close()


def test_roll_is_idempotent(tmp_path):
    db_path = tmp_path / "test2.db"
    conn = sqlite3.connect(str(db_path))
    try:
        _init_db(conn)
        cur = conn.cursor()

        d = "2025-08-14"
        cur.execute(
            "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'close', ?, ?)",
            ("TYU5 Comdty", 111.59375, f"{d} 16:00:00"),
        )
        conn.commit()

        # First roll
        rolled_date, count = roll_latest_close_to_sodtod(conn)
        assert count == 1

        # Second roll: should overwrite same value, still 1 op
        rolled_date2, count2 = roll_latest_close_to_sodtod(conn)
        assert count2 == 1

        row = cur.execute("SELECT price, timestamp FROM pricing WHERE symbol=? AND price_type='sodTod'", ("TYU5 Comdty",)).fetchone()
        assert row == (111.59375, f"{d} 06:00:00")
    finally:
        conn.close()

