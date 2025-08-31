import sqlite3
from datetime import datetime, date

import pandas as pd

from lib.trading.pnl_fifo_lifo.config import (
    PNL_MULTIPLIER,
    get_pnl_multiplier,
)
from lib.trading.pnl_fifo_lifo.pnl_engine import (
    process_new_trade,
    calculate_daily_simple_unrealized_pnl,
)
from lib.trading.pnl_fifo_lifo.data_manager import (
    create_all_tables,
    perform_eod_settlement,
    update_daily_position,
)


def _process_long_then_close(conn: sqlite3.Connection, symbol: str, entry: float, exit_: float, qty: float) -> float:
    """Helper: open a long then close it, returning realized PnL for the closing trade (FIFO)."""
    # Open long
    open_trade = {
        'transactionId': 1,
        'symbol': symbol,
        'price': entry,
        'quantity': qty,
        'buySell': 'B',
        'sequenceId': '20250814-1',
        'time': '2025-08-14 10:00:00.000',
        'fullPartial': 'full',
    }
    process_new_trade(conn, open_trade, 'fifo', '2025-08-14 10:00:00')

    # Close long (sell)
    close_trade = {
        'transactionId': 2,
        'symbol': symbol,
        'price': exit_,
        'quantity': qty,
        'buySell': 'S',
        'sequenceId': '20250814-2',
        'time': '2025-08-14 11:00:00.000',
        'fullPartial': 'full',
    }
    realized = process_new_trade(conn, close_trade, 'fifo', '2025-08-14 11:00:00')
    return sum(r['realizedPnL'] for r in realized)


def test_get_pnl_multiplier_override_map():
    assert get_pnl_multiplier('TYU5 Comdty') == PNL_MULTIPLIER
    assert get_pnl_multiplier('TUU5 Comdty') == 2000


def test_realized_pnl_uses_per_symbol_multiplier_fifo():
    conn = sqlite3.connect(':memory:')
    try:
        create_all_tables(conn)

        entry = 112.50
        exit_ = 112.75
        qty = 10

        # Control symbol (unchanged behavior): TYU5 uses default multiplier
        ty_symbol = 'TYU5 Comdty'
        ty_realized = _process_long_then_close(conn, ty_symbol, entry, exit_, qty)
        assert ty_realized == (exit_ - entry) * qty * PNL_MULTIPLIER

        # Override symbol: TUU5 uses 2000
        # Reset tables for clean state
        create_all_tables(conn)
        tu_symbol = 'TUU5 Comdty'
        tu_realized = _process_long_then_close(conn, tu_symbol, entry, exit_, qty)
        assert tu_realized == (exit_ - entry) * qty * 2000
    finally:
        conn.close()


def test_daily_simple_unrealized_uses_per_symbol_multiplier():
    # Build a minimal positions_df for two symbols with the same entry price
    positions_df = pd.DataFrame([
        {
            'sequenceId': 'seq-1',
            'symbol': 'TYU5 Comdty',
            'quantity': 10,
            'price': 100.0,
            'buySell': 'B',
        },
        {
            'sequenceId': 'seq-2',
            'symbol': 'TUU5 Comdty',
            'quantity': 10,
            'price': 100.0,
            'buySell': 'B',
        },
    ])

    settle_prices = {
        'TYU5 Comdty': 101.0,
        'TUU5 Comdty': 101.0,
    }

    results = calculate_daily_simple_unrealized_pnl(positions_df, settle_prices)
    by_symbol = {r['symbol']: r for r in results}

    assert by_symbol['TYU5 Comdty']['unrealizedPnL'] == (101.0 - 100.0) * 10 * PNL_MULTIPLIER
    assert by_symbol['TUU5 Comdty']['unrealizedPnL'] == (101.0 - 100.0) * 10 * 2000


def test_eod_settlement_updates_daily_positions_with_override():
    conn = sqlite3.connect(':memory:')
    try:
        create_all_tables(conn)

        # Create open positions (long 10 @ 100) for both symbols
        for idx, symbol in enumerate(['TYU5 Comdty', 'TUU5 Comdty'], start=1):
            open_trade = {
                'transactionId': idx,
                'symbol': symbol,
                'price': 100.0,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': f'20250814-{idx}',
                'time': '2025-08-14 10:00:00.000',
                'fullPartial': 'full',
            }
            process_new_trade(conn, open_trade, 'fifo', '2025-08-14 10:00:00')
            process_new_trade(conn, open_trade, 'lifo', '2025-08-14 10:00:00')

        # Seed daily_positions rows so perform_eod_settlement's UPDATE targets exist
        trade_date_str = '2025-08-14'
        for method in ['fifo', 'lifo']:
            update_daily_position(conn, trade_date_str, 'TYU5 Comdty', method, 0, 0)
            update_daily_position(conn, trade_date_str, 'TUU5 Comdty', method, 0, 0)
        conn.commit()

        # Close prices for the EOD settlement
        settlement_date = date(2025, 8, 14)
        close_prices = {
            'TYU5 Comdty': 101.0,
            'TUU5 Comdty': 101.0,
        }

        perform_eod_settlement(conn, settlement_date, close_prices)

        # Verify unrealized_pnl stored with correct multipliers
        df = pd.read_sql_query(
            "SELECT symbol, method, unrealized_pnl FROM daily_positions WHERE date = ?",
            conn,
            params=(trade_date_str,),
        )
        assert not df.empty

        def _expected(symbol: str) -> float:
            mult = 2000 if symbol == 'TUU5 Comdty' else PNL_MULTIPLIER
            return (101.0 - 100.0) * 10 * mult

        for _, row in df.iterrows():
            assert row['unrealized_pnl'] == _expected(row['symbol'])
    finally:
        conn.close()

