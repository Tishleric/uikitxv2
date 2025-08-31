"""
SOD roll utilities: copy latest close prices to sodTod at start of trading day.

This module mirrors the semantics proven in scripts/rebuild_historical_pnl.py:
- For the latest trading date that has close prices, write sodTod prices equal
  to those closes, using a timestamp of "YYYY-MM-DD 06:00:00" for that date.

Public functions here are intentionally small and side-effect free (except DB IO)
to support unit testing and reuse by a long-running service script.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Iterable, Optional, Tuple
import sqlite3


def _query_single_value(conn: sqlite3.Connection, query: str, params: Tuple = ()) -> Optional[str]:
    cursor = conn.cursor()
    row = cursor.execute(query, params).fetchone()
    return row[0] if row and row[0] is not None else None


def get_latest_close_date(conn: sqlite3.Connection) -> Optional[date]:
    """Return the most recent DATE(timestamp) that has any price_type='close'."""
    latest_str = _query_single_value(
        conn,
        "SELECT MAX(DATE(timestamp)) FROM pricing WHERE price_type = 'close'",
    )
    return datetime.strptime(latest_str, "%Y-%m-%d").date() if latest_str else None


def already_rolled_for_date(conn: sqlite3.Connection, d: date) -> bool:
    """Return True if any sodTod rows exist dated on d (DATE(timestamp) == d)."""
    count_str = _query_single_value(
        conn,
        "SELECT COUNT(1) FROM pricing WHERE price_type='sodTod' AND DATE(timestamp)=?",
        (d.strftime("%Y-%m-%d"),),
    )
    count = int(count_str) if count_str is not None else 0
    return count > 0


def _load_closes_for_date(conn: sqlite3.Connection, d: date) -> Dict[str, float]:
    """Load all close prices for symbols dated on d (DATE(timestamp) == d)."""
    cursor = conn.cursor()
    dfmt = d.strftime("%Y-%m-%d")
    rows = cursor.execute(
        """
        SELECT symbol, price
        FROM pricing
        WHERE price_type='close' AND DATE(timestamp)=?
        """,
        (dfmt,),
    ).fetchall()
    return {sym: float(px) for sym, px in rows}


def roll_latest_close_to_sodtod(conn: sqlite3.Connection) -> Tuple[Optional[date], int]:
    """Copy latest close prices to sodTod with a 06:00:00 timestamp for that date.

    Returns (rolled_date, num_symbols_updated). If no close exists, (None, 0).
    Safe to run multiple times; it overwrites sodTod for the same date.
    """
    latest_date = get_latest_close_date(conn)
    if latest_date is None:
        return None, 0

    closes = _load_closes_for_date(conn, latest_date)
    if not closes:
        return latest_date, 0

    cursor = conn.cursor()
    ts = f"{latest_date.strftime('%Y-%m-%d')} 06:00:00"
    updated = 0
    for symbol, price in closes.items():
        cursor.execute(
            """
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'sodTod', ?, ?)
            """,
            (symbol, price, ts),
        )
        updated += 1

    conn.commit()
    return latest_date, updated

