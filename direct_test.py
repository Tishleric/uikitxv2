#!/usr/bin/env python3

# Direct test of P&L functionality
import sys
sys.path.insert(0, '.')

from lib.trading.pnl_fifo_lifo.main import process_multiple_csvs
from lib.trading.pnl_fifo_lifo.data_manager import (
    create_all_tables, view_daily_positions
)
import sqlite3
from datetime import datetime

# Historical prices
close_prices = {
    datetime(2025, 7, 21).date(): 111.1875,
    datetime(2025, 7, 22).date(): 111.40625,
    datetime(2025, 7, 23).date(): 111.015625,
    datetime(2025, 7, 24).date(): 110.828125,
    datetime(2025, 7, 25).date(): 110.984375
}

# Create database
print("Creating database...")
conn = sqlite3.connect('trades.db')
create_all_tables(conn)

# Process trades
print("\nProcessing trades from data/input/trade_ledger...")
trades_df = process_multiple_csvs('data/input/trade_ledger', conn, close_prices)

# View results
print("\nFetching results...")
daily_pos = view_daily_positions(conn)

if not daily_pos.empty:
    print("\nDaily Positions:")
    print("-" * 80)
    print(daily_pos[['date', 'method', 'open_position', 'closed_position', 'realized_pnl', 'unrealized_pnl']])
    
    # Summary
    print("\n" + "="*50)
    for method in ['fifo', 'lifo']:
        method_data = daily_pos[daily_pos['method'] == method]
        if not method_data.empty:
            total_realized = method_data['realized_pnl'].sum()
            final_unrealized = method_data.iloc[-1]['unrealized_pnl']
            print(f"\n{method.upper()} Method Summary:")
            print(f"  Total Realized P&L: ${total_realized:,.2f}")
            print(f"  Final Unrealized P&L: ${final_unrealized:,.2f}")
            print(f"  Total P&L: ${total_realized + final_unrealized:,.2f}")

conn.close()
print("\nTest completed!") 