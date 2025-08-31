#!/usr/bin/env python3
"""
Perpetual SOD roll service.

Behavior:
- Sleeps most of the time.
- Around 17:00 Chicago time, it attempts to copy latest 'close' prices to 'sodTod'
  for the latest trading date, mirroring rebuild_historical_pnl.py semantics
  (timestamp set to YYYY-MM-DD 06:00:00 of that latest close date).
- Idempotent: safe to run repeatedly; it overwrites sodTod for that date.
- Emits a Redis 'positions:changed' signal to refresh the aggregator.

No dependencies on file watchers; minimal risk of breaking existing flows.
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta

import pytz

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_fifo_lifo import config
from lib.trading.pnl_fifo_lifo.sod_roll import roll_latest_close_to_sodtod, get_latest_close_date, already_rolled_for_date


logger = logging.getLogger(__name__)


CHICAGO_TZ = pytz.timezone('America/Chicago')


def _publish_positions_changed():
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.publish("positions:changed", "sod_roll")
        logger.info("Published positions:changed (sod_roll)")
    except Exception as e:
        logger.warning(f"Failed to publish Redis signal: {e}")


def _now_cdt() -> datetime:
    return datetime.now(CHICAGO_TZ)


def _should_attempt_roll(now_cdt: datetime) -> bool:
    """Return True if we are in the activation window to run the roll once per day.

    Window: from 17:00 to 17:30 Chicago time (inclusive). Outside, do nothing.
    """
    return now_cdt.hour == 17 or (now_cdt.hour == 17 and now_cdt.minute <= 30)


def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_NAME, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting SOD Roll Service (perpetual)")

    last_success_date_str = None

    while True:
        try:
            now = _now_cdt()

            # Attempt only during the activation window, and only once per day
            if _should_attempt_roll(now):
                with _connect_db() as conn:
                    latest_close_date = get_latest_close_date(conn)
                    if latest_close_date is None:
                        logger.warning("No close prices found yet; will retry")
                    else:
                        # Skip if we've already rolled sodTod for that date in this run
                        if last_success_date_str == latest_close_date.strftime('%Y-%m-%d'):
                            pass
                        else:
                            rolled_date, count = roll_latest_close_to_sodtod(conn)
                            if rolled_date is not None:
                                logger.info(f"SOD roll completed for {rolled_date} -> {count} symbols")
                                _publish_positions_changed()
                                last_success_date_str = rolled_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Unexpected error in SOD Roll Service loop: {e}", exc_info=True)

        # Sleep a minute between checks to keep CPU/IO minimal
        time.sleep(60)

    # Unreachable
    # return 0


if __name__ == '__main__':
    sys.exit(main())

