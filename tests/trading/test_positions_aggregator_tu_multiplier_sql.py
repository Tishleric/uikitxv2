import sqlite3
from datetime import date, datetime

import pandas as pd
import pytest

from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator


def _create_minimal_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # trades tables (minimal subset)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trades_fifo (
            transactionId INTEGER,
            symbol TEXT,
            price REAL,
            original_price REAL,
            quantity REAL,
            buySell TEXT,
            sequenceId TEXT PRIMARY KEY,
            time TEXT,
            original_time TEXT,
            fullPartial TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trades_lifo AS SELECT * FROM trades_fifo WHERE 0
        """
    )
    # realized tables (aggregator reads these)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS realized_fifo (
            symbol TEXT,
            sequenceIdBeingOffset TEXT,
            sequenceIdDoingOffsetting TEXT,
            partialFull TEXT,
            quantity REAL,
            entryPrice REAL,
            exitPrice REAL,
            realizedPnL REAL,
            timestamp TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS realized_lifo AS SELECT * FROM realized_fifo WHERE 0
        """
    )
    # pricing (for sodTod join)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pricing (
            symbol TEXT,
            price_type TEXT,
            price REAL,
            timestamp TEXT,
            PRIMARY KEY (symbol, price_type)
        )
        """
    )
    conn.commit()


def _insert_test_rows(conn: sqlite3.Connection, trading_day: str) -> None:
    cur = conn.cursor()

    # Pricing SOD for TU and TY
    cur.execute(
        "INSERT OR REPLACE INTO pricing(symbol, price_type, price, timestamp) VALUES (?,?,?,?)",
        ("TUZ5 Comdty", "sodTod", 100.0, f"{trading_day} 14:00:00"),
    )
    cur.execute(
        "INSERT OR REPLACE INTO pricing(symbol, price_type, price, timestamp) VALUES (?,?,?,?)",
        ("TYU5 Comdty", "sodTod", 100.0, f"{trading_day} 14:00:00"),
    )

    # Realized rows with today's trading day in timestamp, non-equal entry day via sequenceIdBeingOffset
    # Use exitPrice 101, entryPrice 100, qty 1, realizedPnL positive (to take the first branch)
    for tbl, sym in [("realized_fifo", "TUZ5 Comdty"), ("realized_lifo", "TUZ5 Comdty"), (
        "realized_fifo", "TYU5 Comdty"), ("realized_lifo", "TYU5 Comdty")]:
        cur.execute(
            f"""
            INSERT INTO {tbl}
            (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, partialFull,
             quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sym,
                "20240820-0001",  # entry day != trading_day to trigger Pmax branch
                "{td}-0001".format(td=trading_day.replace("-", "")),
                "full",
                1.0,
                100.0,
                101.0,
                1000.0,
                f"{trading_day} 11:00:00",
            ),
        )

    conn.commit()


def _monkeypatch_trading_day(monkeypatch, target_date: date) -> None:
    # Aggregator imports get_trading_day directly; patch it in the module namespace
    import lib.trading.pnl_fifo_lifo.positions_aggregator as pa_mod

    def _fake_get_trading_day(_dt):
        return target_date

    monkeypatch.setattr(pa_mod, "get_trading_day", _fake_get_trading_day)


def test_positions_aggregator_uses_root_based_tu_multiplier(tmp_path, monkeypatch):
    # Prepare temp DB
    db_dir = tmp_path / "db"
    db_dir.mkdir(exist_ok=True)
    db_path = str(db_dir / "trades.db")
    conn = sqlite3.connect(db_path)
    try:
        _create_minimal_schema(conn)
        # Fix trading day as '2025-08-21'
        fixed_day = date(2025, 8, 21)
        _insert_test_rows(conn, trading_day=fixed_day.strftime('%Y-%m-%d'))
    finally:
        conn.close()

    # Patch trading day in aggregator to our fixed_day
    _monkeypatch_trading_day(monkeypatch, fixed_day)

    # Run load
    agg = PositionsAggregator(trades_db_path=db_path)
    agg._load_positions_from_db()

    # Validate realized PnL scaling: TU should be 2000, TY 1000 for 1pt * qty 1
    df = agg.positions_cache
    # We expect at least these two symbols present
    tu_row = df[df['symbol'] == 'TUZ5 Comdty']
    ty_row = df[df['symbol'] == 'TYU5 Comdty']

    assert not tu_row.empty
    assert not ty_row.empty

    # FIFO realized PnL
    assert abs(float(tu_row['fifo_realized_pnl'].iloc[0]) - 2000.0) < 1e-6
    assert abs(float(ty_row['fifo_realized_pnl'].iloc[0]) - 1000.0) < 1e-6

    # LIFO realized PnL
    assert abs(float(tu_row['lifo_realized_pnl'].iloc[0]) - 2000.0) < 1e-6
    assert abs(float(ty_row['lifo_realized_pnl'].iloc[0]) - 1000.0) < 1e-6


