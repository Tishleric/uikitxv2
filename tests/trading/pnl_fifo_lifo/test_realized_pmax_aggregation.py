import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

import pandas as pd

from lib.trading.pnl_fifo_lifo import data_manager
from lib.trading.pnl_fifo_lifo import positions_aggregator as agg_mod
from lib.trading.pnl_fifo_lifo.config import PNL_MULTIPLIER


def _make_timestamp_for_trading_day(target_trading_day: datetime.date, hour: int = 12) -> str:
    """Return a timestamp string that maps to the given trading day under 5pm boundary logic.

    Using hour < 17 ensures DATE(ts, case...) = target_trading_day.
    """
    return f"{target_trading_day.strftime('%Y-%m-%d')} {hour:02d}:00:00"


def _make_prev_trading_day(ts_date: datetime.date) -> datetime.date:
    """Compute a previous calendar date to represent an entry before today's trading day."""
    return ts_date - timedelta(days=1)


def _setup_db_with_schema(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    data_manager.create_all_tables(conn)
    return conn


def _insert_pricing_sodtod(conn: sqlite3.Connection, symbol: str, sod_price: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'sodTod', ?, ?)",
        (symbol, sod_price, f"{datetime.now().strftime('%Y-%m-%d')} 14:00:00"),
    )
    conn.commit()


def _insert_entry_trade(conn: sqlite3.Connection, method: str, sequence_id: str, symbol: str,
                        price: float, buy_sell: str, entry_ts: str) -> None:
    table = f"trades_{method}"
    # quantity 0 to avoid creating open positions while still providing joinable metadata
    conn.execute(
        f"""
        INSERT INTO {table} (transactionId, symbol, price, original_price, quantity, buySell, sequenceId, time, original_time, fullPartial)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'full')
        """,
        (1, symbol, price, price, 0, buy_sell, sequence_id, entry_ts, entry_ts),
    )
    conn.commit()


def _insert_realized_row(conn: sqlite3.Connection, method: str, symbol: str,
                         seq_entry: str, seq_exit: str, qty: float,
                         entry_price: float, exit_price: float, realized_pnl: float,
                         realized_ts: str) -> None:
    table = f"realized_{method}"
    conn.execute(
        f"""
        INSERT INTO {table} (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
        VALUES (?, ?, ?, 'full', ?, ?, ?, ?, ?)
        """,
        (symbol, seq_entry, seq_exit, qty, entry_price, exit_price, realized_pnl, realized_ts),
    )
    conn.commit()


def _run_aggregation(db_path: str, realized_pmax_enabled: bool) -> pd.DataFrame:
    # Toggle aggregator flag locally (module-level variable)
    original_flag = getattr(agg_mod, "REALIZED_PMAX_ENABLED", True)
    try:
        agg_mod.REALIZED_PMAX_ENABLED = realized_pmax_enabled
        aggregator = agg_mod.PositionsAggregator(trades_db_path=db_path)
        aggregator._load_positions_from_db()
        return aggregator.positions_cache.copy()
    finally:
        agg_mod.REALIZED_PMAX_ENABLED = original_flag


def test_fifo_long_entry_yesterday_rebases_to_sod():
    symbol = 'TYU5 Comdty'
    qty = 10
    entry_price = 100.0
    sod_price = 105.0
    exit_price = 110.0

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = _setup_db_with_schema(db_path)
        try:
            # Determine target trading day used by aggregator now
            trading_day = data_manager.get_trading_day(datetime.now())
            realized_ts = _make_timestamp_for_trading_day(trading_day)
            entry_day = _make_prev_trading_day(trading_day)
            entry_ts = _make_timestamp_for_trading_day(entry_day)

            _insert_pricing_sodtod(conn, symbol, sod_price)
            _insert_entry_trade(conn, 'fifo', 'SEQ1', symbol, entry_price, 'B', entry_ts)
            raw_realized = (exit_price - entry_price) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'fifo', symbol, 'SEQ1', 'SEQ2', qty, entry_price, exit_price, raw_realized, realized_ts)

            # Pmax ON → expected rebasing to SOD: (exit - SOD) * qty * 1000
            df = _run_aggregation(db_path, realized_pmax_enabled=True)
            row = df[df['symbol'] == symbol].iloc[0]
            expected = (exit_price - sod_price) * qty * PNL_MULTIPLIER
            assert round(row['fifo_realized_pnl'], 6) == round(expected, 6)

            # Pmax OFF → original raw realized
            df_raw = _run_aggregation(db_path, realized_pmax_enabled=False)
            row_raw = df_raw[df_raw['symbol'] == symbol].iloc[0]
            assert round(row_raw['fifo_realized_pnl'], 6) == round(raw_realized, 6)
        finally:
            conn.close()


def test_fifo_long_entry_today_does_not_rebase():
    symbol = 'TYU5 Comdty'
    qty = 8
    entry_price = 103.0
    sod_price = 105.0
    exit_price = 110.0

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test2.db')
        conn = _setup_db_with_schema(db_path)
        try:
            trading_day = data_manager.get_trading_day(datetime.now())
            realized_ts = _make_timestamp_for_trading_day(trading_day)
            entry_ts = _make_timestamp_for_trading_day(trading_day)

            _insert_pricing_sodtod(conn, symbol, sod_price)
            _insert_entry_trade(conn, 'fifo', 'SEQ10', symbol, entry_price, 'B', entry_ts)
            raw_realized = (exit_price - entry_price) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'fifo', symbol, 'SEQ10', 'SEQ11', qty, entry_price, exit_price, raw_realized, realized_ts)

            # Pmax ON but entry is today → remains raw
            df = _run_aggregation(db_path, realized_pmax_enabled=True)
            row = df[df['symbol'] == symbol].iloc[0]
            assert round(row['fifo_realized_pnl'], 6) == round(raw_realized, 6)
        finally:
            conn.close()


def test_fifo_short_entry_yesterday_rebases_sign_correctly():
    symbol = 'TYU5 Comdty'
    qty = 5
    entry_price = 100.0
    sod_price = 105.0
    exit_price = 110.0  # covering higher → loss

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test3.db')
        conn = _setup_db_with_schema(db_path)
        try:
            trading_day = data_manager.get_trading_day(datetime.now())
            realized_ts = _make_timestamp_for_trading_day(trading_day)
            entry_day = _make_prev_trading_day(trading_day)
            entry_ts = _make_timestamp_for_trading_day(entry_day)

            _insert_pricing_sodtod(conn, symbol, sod_price)
            _insert_entry_trade(conn, 'fifo', 'SEQ20', symbol, entry_price, 'S', entry_ts)
            raw_realized = (entry_price - exit_price) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'fifo', symbol, 'SEQ20', 'SEQ21', qty, entry_price, exit_price, raw_realized, realized_ts)

            df = _run_aggregation(db_path, realized_pmax_enabled=True)
            row = df[df['symbol'] == symbol].iloc[0]
            expected = (sod_price - exit_price) * qty * PNL_MULTIPLIER
            assert round(row['fifo_realized_pnl'], 6) == round(expected, 6)
        finally:
            conn.close()


def test_lifo_long_rebases_similarly():
    symbol = 'FVU5 Comdty'
    qty = 7
    entry_price = 109.0
    sod_price = 110.0
    exit_price = 111.0

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test4.db')
        conn = _setup_db_with_schema(db_path)
        try:
            trading_day = data_manager.get_trading_day(datetime.now())
            realized_ts = _make_timestamp_for_trading_day(trading_day)
            entry_day = _make_prev_trading_day(trading_day)
            entry_ts = _make_timestamp_for_trading_day(entry_day)

            _insert_pricing_sodtod(conn, symbol, sod_price)
            _insert_entry_trade(conn, 'lifo', 'LSEQ1', symbol, entry_price, 'B', entry_ts)
            raw_realized = (exit_price - entry_price) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'lifo', symbol, 'LSEQ1', 'LSEQ2', qty, entry_price, exit_price, raw_realized, realized_ts)

            df = _run_aggregation(db_path, realized_pmax_enabled=True)
            row = df[df['symbol'] == symbol].iloc[0]
            expected = (exit_price - sod_price) * qty * PNL_MULTIPLIER
            assert round(row['lifo_realized_pnl'], 6) == round(expected, 6)
        finally:
            conn.close()


def test_missing_sod_falls_back_to_entry_price():
    symbol = 'USU5 Comdty'
    qty = 3
    entry_price = 120.0
    exit_price = 121.5

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test5.db')
        conn = _setup_db_with_schema(db_path)
        try:
            trading_day = data_manager.get_trading_day(datetime.now())
            realized_ts = _make_timestamp_for_trading_day(trading_day)
            entry_day = _make_prev_trading_day(trading_day)
            entry_ts = _make_timestamp_for_trading_day(entry_day)

            # No SOD price inserted → COALESCE to entry price
            _insert_entry_trade(conn, 'fifo', 'MSEQ1', symbol, entry_price, 'B', entry_ts)
            raw_realized = (exit_price - entry_price) * qty * PNL_MULTIPLIER
            _insert_realized_row(conn, 'fifo', symbol, 'MSEQ1', 'MSEQ2', qty, entry_price, exit_price, raw_realized, realized_ts)

            df = _run_aggregation(db_path, realized_pmax_enabled=True)
            row = df[df['symbol'] == symbol].iloc[0]
            # With missing SOD, adjusted == raw
            assert round(row['fifo_realized_pnl'], 6) == round(raw_realized, 6)
        finally:
            conn.close()

