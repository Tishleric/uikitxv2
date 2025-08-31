import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables, get_trading_day
from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
from lib.trading.pnl_fifo_lifo.config import PNL_MULTIPLIER


def _today_trading_day() -> str:
    # Use same trading-day boundary as aggregator (via get_trading_day)
    return get_trading_day(datetime.now()).strftime('%Y-%m-%d')


def _yesterday_trading_day() -> str:
    return get_trading_day(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def _ts_for_today() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _seq_for_day(day_str: str) -> str:
    # Construct sequenceId with day prefix
    return f"{day_str.replace('-', '')}-1"


def _insert_pricing(conn: sqlite3.Connection, symbol: str, sod: float, now_price: float | None = None) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'sodTod', ?, ?)",
        (symbol, sod, f"{_yesterday_trading_day()} 06:00:00"),
    )
    if now_price is not None:
        cur.execute(
            "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'now', ?, ?)",
            (symbol, now_price, _ts_for_today()),
        )
    conn.commit()


def _insert_realized_row(conn: sqlite3.Connection, table: str, symbol: str, entry_day: str,
                         qty: float, entry_px: float, exit_px: float, realized: float) -> None:
    seq = _seq_for_day(entry_day)
    conn.execute(
        f"""
        INSERT INTO {table} (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
        VALUES (?, ?, 'TODAYSEQ', 'full', ?, ?, ?, ?, ?)
        """,
        (symbol, seq, qty, entry_px, exit_px, realized, _ts_for_today()),
    )
    conn.commit()


def test_fifo_prior_day_entry_no_trades_row_rebases_to_sod():
    symbol = 'TYU5 Comdty'
    qty = 1
    entry_px = 111.65625  # prior-day short
    exit_px = 111.671875  # cover today (raw realized would be negative)
    sod = 111.59375

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, 'test.db')
        conn = sqlite3.connect(db)
        try:
            create_all_tables(conn)
            _insert_pricing(conn, symbol, sod)

            # Insert realized row directly, no trades_fifo entry for seq -> simulates fully offset lot
            raw_realized = (entry_px - exit_px) * qty * PNL_MULTIPLIER  # short cover raw
            _insert_realized_row(conn, 'realized_fifo', symbol, _yesterday_trading_day(), qty, entry_px, exit_px, raw_realized)

            # Aggregate
            a = PositionsAggregator(db)
            a._load_positions_from_db()
            a._write_positions_to_db(a.positions_cache)

            row = conn.execute(
                "SELECT fifo_realized_pnl FROM positions WHERE symbol=?", (symbol,)
            ).fetchone()
            assert row is not None
            # Expected: (SOD - exit) * qty * 1000 for a prior-day short
            expected = (sod - exit_px) * qty * PNL_MULTIPLIER
            assert round(row[0], 6) == round(expected, 6)
        finally:
            conn.close()


def test_lifo_prior_day_entry_no_trades_row_rebases_to_sod():
    symbol = 'TUU5 Comdty'  # ensure TU multiplier 2000 path is exercised
    qty = 2
    entry_px = 103.8203125  # prior-day short
    exit_px = 103.8671875   # cover today
    sod = 103.8203125

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, 'test_lifo.db')
        conn = sqlite3.connect(db)
        try:
            create_all_tables(conn)
            _insert_pricing(conn, symbol, sod)

            # Insert realized row directly into realized_lifo
            raw_realized = (entry_px - exit_px) * qty * 2000  # TU multiplier
            _insert_realized_row(conn, 'realized_lifo', symbol, _yesterday_trading_day(), qty, entry_px, exit_px, raw_realized)

            a = PositionsAggregator(db)
            a._load_positions_from_db()
            a._write_positions_to_db(a.positions_cache)

            row = conn.execute(
                "SELECT lifo_realized_pnl FROM positions WHERE symbol=?", (symbol,)
            ).fetchone()
            assert row is not None
            expected = (sod - exit_px) * qty * 2000
            assert round(row[0], 6) == round(expected, 6)
        finally:
            conn.close()


def test_missing_sod_falls_back_to_raw():
    symbol = 'USU5 Comdty'
    qty = 1
    entry_px = 115.0
    exit_px = 115.125

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, 'test_missing_sod.db')
        conn = sqlite3.connect(db)
        try:
            create_all_tables(conn)
            # No SOD insert
            raw_realized = (entry_px - exit_px) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'realized_fifo', symbol, _yesterday_trading_day(), qty, entry_px, exit_px, raw_realized)

            a = PositionsAggregator(db)
            a._load_positions_from_db()
            a._write_positions_to_db(a.positions_cache)

            row = conn.execute(
                "SELECT fifo_realized_pnl FROM positions WHERE symbol=?", (symbol,)
            ).fetchone()
            assert row is not None
            # Fallback should keep raw when SOD missing
            assert round(row[0], 6) == round(raw_realized, 6)
        finally:
            conn.close()

