"""
Manually perform a safe SOD roll into the pricing table, with dry-run support.

Semantics:
1) Prefer moving sodTom -> sodTod for the latest sodTom date (preserving timestamps),
   then delete those sodTom rows.
2) If no sodTom exists for the latest close date, fall back to copying close -> sodTod
   with a 06:00:00 timestamp for that date (idempotent per (symbol, 'sodTod')).

Usage:
  python scripts/diagnostics/manual_sod_roll_now.py --db trades.db --execute

Defaults to dry-run unless --execute is provided. Always prints summary counts.
Exit codes:
  0 = Success (or dry-run okay)
  2 = No source rows available (nothing to do)
  3 = Schema/connection error
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from typing import Tuple


def _q1(conn: sqlite3.Connection, q: str, p: Tuple = ()):  # fetchone col0
    cur = conn.cursor()
    row = cur.execute(q, p).fetchone()
    return row[0] if row else None


def _count_on(conn: sqlite3.Connection, price_type: str, date_str: str) -> int:
    cur = conn.cursor()
    return cur.execute(
        "SELECT COUNT(1) FROM pricing WHERE price_type=? AND DATE(timestamp)=?",
        (price_type, date_str),
    ).fetchone()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual SOD roll (safe)")
    parser.add_argument("--db", default="trades.db", help="Path to SQLite DB (default: trades.db)")
    parser.add_argument("--execute", action="store_true", help="Apply changes (otherwise dry-run)")
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

        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if "pricing" not in tables:
            print("ERROR: pricing table not found")
            return 3

        latest_sodtom_date = _q1(conn, "SELECT MAX(DATE(timestamp)) FROM pricing WHERE price_type='sodTom'")
        latest_close_date = _q1(conn, "SELECT MAX(DATE(timestamp)) FROM pricing WHERE price_type='close'")
        print("latest_sodTom_date =", latest_sodtom_date)
        print("latest_close_date  =", latest_close_date)

        # Select source date: prefer sodTom if present else close
        source_date = latest_sodtom_date or latest_close_date
        if not source_date:
            print("Nothing to roll: no sodTom or close found")
            return 2

        n_sodTom = _count_on(conn, "sodTom", source_date)
        n_close = _count_on(conn, "close", source_date)
        n_sodTod_pre = _count_on(conn, "sodTod", source_date)
        print("pre counts on source date:", {"sodTom": n_sodTom, "close": n_close, "sodTod": n_sodTod_pre})

        if not args.execute:
            print("DRY RUN. No changes applied. Re-run with --execute to apply.")
            return 0

        conn.execute("BEGIN")

        # Clear any existing sodTod rows for that date to avoid mixed timestamps/sources
        cur.execute("DELETE FROM pricing WHERE price_type='sodTod' AND DATE(timestamp)=?", (source_date,))

        moved = 0
        if n_sodTom > 0:
            # Copy sodTom -> sodTod preserving timestamps; then delete sodTom
            cur.execute(
                """
                INSERT OR REPLACE INTO pricing(symbol, price_type, price, timestamp)
                SELECT symbol, 'sodTod', price, timestamp
                FROM pricing
                WHERE price_type='sodTom' AND DATE(timestamp)=?
                """,
                (source_date,),
            )
            moved = cur.execute("SELECT changes()").fetchone()[0]
            cur.execute("DELETE FROM pricing WHERE price_type='sodTom' AND DATE(timestamp)=?", (source_date,))
        else:
            # Fallback: copy close -> sodTod with 06:00 timestamp
            cur.execute(
                """
                INSERT OR REPLACE INTO pricing(symbol, price_type, price, timestamp)
                SELECT symbol, 'sodTod', price, SUBSTR(timestamp,1,10) || ' 06:00:00'
                FROM pricing
                WHERE price_type='close' AND DATE(timestamp)=?
                """,
                (source_date,),
            )
            moved = cur.execute("SELECT changes()").fetchone()[0]

        conn.commit()
        n_sodTod_post = _count_on(conn, "sodTod", source_date)
        n_sodTom_post = _count_on(conn, "sodTom", source_date)
        times_sodTod = [r[0] for r in cur.execute(
            "SELECT DISTINCT TIME(timestamp) FROM pricing WHERE price_type='sodTod' AND DATE(timestamp)=?",
            (source_date,)).fetchall()]

        print("moved_to_sodTod =", moved)
        print("post counts on date:", {"sodTod": n_sodTod_post, "sodTom": n_sodTom_post})
        print("sodTod times on date:", times_sodTod)
        return 0

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

