"""
Verify SOD roll results in a SQLite trades database.

This script performs read-only diagnostics:
- Prints working directory and resolved DB path
- Shows PRAGMA database_list (actual file path SQLite opened)
- Finds latest close date D
- Compares counts of close vs sodTod on D
- Lists distinct sodTod times on D and the latest sodTod date overall

Usage:
  python scripts/diagnostics/verify_sod_roll.py --db trades.db

Exit codes:
  0 = PASS (counts match)
  2 = MISMATCH (counts differ)
  3 = SCHEMA/ENV ISSUE (pricing table missing or no close rows)
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from typing import Tuple, List


def _get_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    return [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]


def _query_one(conn: sqlite3.Connection, query: str, params: Tuple = ()):
    cur = conn.cursor()
    row = cur.execute(query, params).fetchone()
    return row[0] if row else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SOD roll results")
    parser.add_argument("--db", default="trades.db", help="Path to SQLite DB (default: trades.db)")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    print(f"cwd = {os.getcwd()}")
    print(f"db_path = {db_path}")

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(f"ERROR: failed to connect to DB: {e}")
        return 3

    try:
        cur = conn.cursor()
        print("PRAGMA database_list =", cur.execute("PRAGMA database_list").fetchall())

        tables = _get_tables(conn)
        print("tables =", tables)
        if "pricing" not in tables:
            print("ERROR: pricing table not found")
            return 3

        latest_close_date = _query_one(
            conn, "SELECT MAX(DATE(timestamp)) FROM pricing WHERE price_type='close'"
        )
        print("latest_close_date =", latest_close_date)
        if not latest_close_date:
            print("ERROR: No close rows found; cannot verify SOD roll")
            return 3

        close_cnt = _query_one(
            conn,
            "SELECT COUNT(1) FROM pricing WHERE price_type='close' AND DATE(timestamp)=?",
            (latest_close_date,),
        )
        sodtod_cnt = _query_one(
            conn,
            "SELECT COUNT(1) FROM pricing WHERE price_type='sodTod' AND DATE(timestamp)=?",
            (latest_close_date,),
        )
        sodtod_times = [
            r[0]
            for r in cur.execute(
                "SELECT DISTINCT TIME(timestamp) FROM pricing WHERE price_type='sodTod' AND DATE(timestamp)=?",
                (latest_close_date,),
            ).fetchall()
        ]
        max_sodtod_date = _query_one(
            conn, "SELECT MAX(DATE(timestamp)) FROM pricing WHERE price_type='sodTod'"
        )

        print("counts =", {"close": close_cnt, "sodTod": sodtod_cnt})
        print("sodTod_times_on_latest =", sodtod_times)
        print("max_sodTod_date =", max_sodtod_date)

        if close_cnt == sodtod_cnt and sodtod_cnt is not None:
            print("RESULT = PASS (sodTod matches close count on latest date)")
            return 0
        else:
            print("RESULT = MISMATCH (sodTod count differs from close count on latest date)")
            return 2

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

