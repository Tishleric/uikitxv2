import io
import os
import sqlite3
import tempfile
import pandas as pd

from pathlib import Path

from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceFileHandler


def _write_temp_csv(tmp_path: Path, name: str, df: pd.DataFrame) -> Path:
    fpath = tmp_path / name
    df.to_csv(fpath, index=False)
    return fpath


def test_month_coded_futures_symbol_to_bloomberg(tmp_path: Path):
    # Prepare a minimal futures CSV with month-coded SYMBOL
    data = pd.DataFrame([
        {"SYMBOL": "TYU5", "PX_SETTLE_DEC": 110.125, "PX_300_DEC": 110.10, "Settle Price = Today": "Y"},
        {"SYMBOL": "TYZ5", "PX_SETTLE_DEC": None,    "PX_300_DEC": 110.25, "Settle Price = Today": "N"},
        {"SYMBOL": "FVZ5", "PX_SETTLE_DEC": 109.50,  "PX_300_DEC": 109.40, "Settle Price = Today": ""},
    ])

    csv_path = _write_temp_csv(tmp_path, "Futures_20250101_1400.csv", data)

    # Handler needs a db path but we only call the parsing method here
    handler = ClosePriceFileHandler(db_path=str(tmp_path / "trades.db"), startup_time=0.0)

    prices = handler._process_futures_file(csv_path)

    assert prices.get("TYU5 Comdty") == 110.125
    assert prices.get("TYZ5 Comdty") == 110.25
    assert prices.get("FVZ5 Comdty") == 109.50


def test_update_prices_inserts_now_close(tmp_path: Path):
    # Create a small in-memory-like DB on disk for sqlite3
    db_path = str(tmp_path / "trades.db")
    conn = sqlite3.connect(db_path)
    try:
        # Minimal schema for pricing table
        conn.execute(
            """
            CREATE TABLE pricing (
                symbol TEXT,
                price_type TEXT,
                price REAL,
                timestamp TEXT,
                PRIMARY KEY (symbol, price_type)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    handler = ClosePriceFileHandler(db_path=db_path, startup_time=0.0)

    prices = {
        "TYU5 Comdty": 110.125,
        "TYZ5 Comdty": 110.25,
    }

    # Use a dummy date/hour
    handler._update_prices(prices, date_str="20250101", hour=14)

    # Verify rows exist
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT symbol, price_type, price FROM pricing ORDER BY symbol, price_type").fetchall()
        # We expect roll_2pm_prices logic to upsert close and sodTom to the same value at 2pm
        # Here we just ensure entries exist for 'close' and 'sodTom' per symbol
        got = {(r[0], r[1]) for r in rows}
        assert ("TYU5 Comdty", "close") in got
        assert ("TYU5 Comdty", "sodTom") in got
        assert ("TYZ5 Comdty", "close") in got
        assert ("TYZ5 Comdty", "sodTom") in got
    finally:
        conn.close()


