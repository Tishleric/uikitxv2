import sqlite3
from datetime import datetime

from scripts.dev_inject_close_price import inject_close_price


def _create_pricing(conn: sqlite3.Connection):
    conn.execute(
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


def test_dev_inject_close_price_sets_close_and_sodtom_for_close_type(tmp_path):
    db_path = str(tmp_path / "trades.db")
    conn = sqlite3.connect(db_path)
    try:
        _create_pricing(conn)
    finally:
        conn.close()

    # Inject for TYZ5
    inject_close_price(db_path, "TYZ5 Comdty", 110.25, price_type="close")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT symbol, price_type, price, timestamp FROM pricing WHERE symbol = 'TYZ5 Comdty'"
        ).fetchall()
        types = {r[1] for r in rows}
        assert 'close' in types and 'sodTom' in types
        prices = {r[1]: r[2] for r in rows}
        assert abs(prices['close'] - 110.25) < 1e-9
        assert abs(prices['sodTom'] - 110.25) < 1e-9
    finally:
        conn.close()


def test_dev_inject_close_price_sets_only_close_for_flash_type(tmp_path):
    db_path = str(tmp_path / "trades.db")
    conn = sqlite3.connect(db_path)
    try:
        _create_pricing(conn)
    finally:
        conn.close()

    inject_close_price(db_path, "TUU5 Comdty", 106.50, price_type="flash")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT symbol, price_type, price FROM pricing WHERE symbol = 'TUU5 Comdty'"
        ).fetchall()
        types = {r[1] for r in rows}
        assert 'close' in types
        assert 'sodTom' not in types
        price_close = [r[2] for r in rows if r[1] == 'close'][0]
        assert abs(price_close - 106.50) < 1e-9
    finally:
        conn.close()





