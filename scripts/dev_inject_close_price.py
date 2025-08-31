#!/usr/bin/env python3
"""
Dev Close-Price Injector

Purpose: Quickly inject a close (2pm) or flash price into trades.db for a
Bloomberg futures/option symbol, then publish a positions refresh signal.

Usage examples:
  python scripts/dev_inject_close_price.py --symbol "TYZ5 Comdty" --price 110.25 --type close
  python scripts/dev_inject_close_price.py --db trades.db --symbol "TUZ5 Comdty" --price 106.5 --type close
"""

import argparse
import logging
import sqlite3
from datetime import datetime


def _publish_positions_changed():
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.publish("positions:changed", "dev_inject_close_price")
    except Exception as e:
        logging.getLogger(__name__).warning("Redis publish failed: %s", e)


def inject_close_price(db_path: str, symbol: str, price: float, price_type: str = "close") -> None:
    """Inject a price for symbol into pricing table.

    If price_type == 'close', replicate 2pm roll behavior by also setting sodTom.
    Otherwise, only set the 'close' record (sufficient for ad-hoc validation).
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.isolation_level = None
        conn.execute("BEGIN")

        # Use today's 2pm timestamp for 'close' and 'sodTom' alignment
        now = datetime.now()
        ts_2pm = now.replace(hour=14, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

        # Always set/replace the close price for convenience
        conn.execute(
            "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'close', ?, ?)",
            (symbol, price, ts_2pm),
        )

        if price_type.lower() == 'close':
            # Mirror roll_2pm_prices behavior by also setting sodTom
            conn.execute(
                "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'sodTom', ?, ?)",
                (symbol, price, ts_2pm),
            )

        conn.commit()
    finally:
        conn.close()

    _publish_positions_changed()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description='Dev injector for close/flash price in trades.db')
    parser.add_argument('--db', default='trades.db', help='Path to trades database')
    parser.add_argument('--symbol', required=True, help='Bloomberg symbol (e.g., "TYZ5 Comdty")')
    parser.add_argument('--price', type=float, required=True, help='Price value to set')
    parser.add_argument('--type', choices=['close', 'flash'], default='close', help='Type of price to set')

    args = parser.parse_args()
    logging.info("Injecting %s price: %s = %.6f into %s", args.type, args.symbol, args.price, args.db)
    inject_close_price(args.db, args.symbol, args.price, args.type)
    logging.info("Done. Published positions:changed (best-effort).")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())





