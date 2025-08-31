"""
Verify FRG UI guard (trading-day filter on positions.last_updated) against a SQLite DB.

- Prints total rows matching (open_position != 0 OR closed_position != 0)
- Prints rows matching the current trading day (5pm CT boundary)
- Prints excluded count and a small sample of excluded symbols

Usage:
  python scripts/diagnostics/verify_frg_ui_guard.py --db trades.db
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from typing import List, Tuple
from datetime import datetime
import pytz

from lib.trading.pnl_fifo_lifo.data_manager import get_trading_day


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify FRG UI guard trading-day filter")
    parser.add_argument("--db", default="trades.db", help="Path to SQLite DB (default: trades.db)")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    print({"cwd": os.getcwd(), "db_path": db_path})

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Compute current trading day in Chicago time
    now_cdt = datetime.now(pytz.timezone("America/Chicago"))
    trading_day = get_trading_day(now_cdt).strftime("%Y-%m-%d")

    # Rows considered candidates pre-filter (open or closed non-zero)
    total = cur.execute(
        "SELECT COUNT(1) FROM positions WHERE open_position != 0 OR closed_position != 0"
    ).fetchone()[0]

    # Apply the same EXISTS-based realized-trade filter the UI uses
    today = cur.execute(
        f"""
        SELECT COUNT(1)
        FROM positions p
        WHERE 
            p.open_position != 0
            OR (
                p.closed_position != 0 AND (
                    EXISTS (
                        SELECT 1 FROM realized_fifo rf
                        WHERE rf.symbol = p.symbol
                          AND DATE(rf.timestamp,
                                   CASE WHEN CAST(strftime('%H', rf.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = ?
                    )
                    OR EXISTS (
                        SELECT 1 FROM realized_lifo rl
                        WHERE rl.symbol = p.symbol
                          AND DATE(rl.timestamp,
                                   CASE WHEN CAST(strftime('%H', rl.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = ?
                    )
                )
            )
        """,
        (trading_day, trading_day),
    ).fetchone()[0]

    excluded = total - today
    print({"trading_day": trading_day, "total": total, "today": today, "excluded": excluded})

    # Show a few excluded symbols for inspection (candidates that do NOT meet today's filter)
    rows: List[Tuple[str, float, float, str]] = cur.execute(
        f"""
        SELECT symbol, open_position, closed_position, last_updated
        FROM positions p
        WHERE (p.open_position != 0 OR p.closed_position != 0)
          AND NOT (
            p.open_position != 0
            OR (
                p.closed_position != 0 AND (
                    EXISTS (
                        SELECT 1 FROM realized_fifo rf
                        WHERE rf.symbol = p.symbol
                          AND DATE(rf.timestamp,
                                   CASE WHEN CAST(strftime('%H', rf.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = ?
                    )
                    OR EXISTS (
                        SELECT 1 FROM realized_lifo rl
                        WHERE rl.symbol = p.symbol
                          AND DATE(rl.timestamp,
                                   CASE WHEN CAST(strftime('%H', rl.timestamp) AS INTEGER) >= 17 
                                        THEN '+1 day' ELSE '+0 day' END) = ?
                    )
                )
            )
          )
        ORDER BY last_updated DESC
        LIMIT 10
        """,
        (trading_day, trading_day),
    ).fetchall()

    if rows:
        print("excluded_sample:")
        for r in rows:
            print(r)
    else:
        print("excluded_sample: []")

    # Specific symbols often inspected
    subset = cur.execute(
        "SELECT symbol, open_position, closed_position, last_updated FROM positions WHERE symbol IN ('USU5 Comdty','TYU5 Comdty')"
    ).fetchall()
    print({"subset": subset})

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

