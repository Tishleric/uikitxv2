"""
Snapshot positions instrument type and timestamps for target symbols.

Run:
  python diagnostics/db_snapshot_positions.py TYZ5 Comdty USZ5 Comdty
or without args to use a default list.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from typing import Sequence


def snapshot(symbols: Sequence[str]) -> None:
    db_path = os.path.join('trades.db')
    if not os.path.exists(db_path):
        print(f"trades.db not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(symbols))
        query = f"""
        SELECT symbol, instrument_type, has_greeks, last_greek_update, last_trade_update, last_updated
        FROM positions
        WHERE symbol IN ({placeholders})
        ORDER BY symbol
        """
        cur.execute(query, list(symbols))
        rows = cur.fetchall()
        if not rows:
            print("No rows found in positions for provided symbols.")
            return
        print("symbol | instrument_type | has_greeks | last_greek_update | last_trade_update | last_updated")
        for r in rows:
            print(' | '.join(str(x) if x is not None else '' for x in r))
    finally:
        conn.close()


def main() -> None:
    symbols = sys.argv[1:]
    if not symbols:
        symbols = ['TYZ5 Comdty', 'USZ5 Comdty']
    snapshot(symbols)


if __name__ == '__main__':
    main()


