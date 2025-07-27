#!/usr/bin/env python3
"""
Simple P&L test to verify the module works correctly
"""

import sys
import os

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from lib.trading.pnl_fifo_lifo import (
        create_all_tables, 
        process_new_trade,
        load_multiple_csvs,
        view_daily_positions,
        process_multiple_csvs
    )
    from lib.trading.pnl_fifo_lifo.main import process_multiple_csvs as main_process_multiple_csvs
    from lib.trading.pnl_fifo_lifo import config
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test database operations
import sqlite3
from datetime import datetime

# Historical close prices
close_prices = {
    datetime(2025, 7, 21).date(): 111.1875,
    datetime(2025, 7, 22).date(): 111.40625,
    datetime(2025, 7, 23).date(): 111.015625,
    datetime(2025, 7, 24).date(): 110.828125,
    datetime(2025, 7, 25).date(): 110.984375
}

# Create database
conn = sqlite3.connect('trades.db')
print("✓ Database connection created")

# Create tables
create_all_tables(conn)
print("✓ Tables created successfully")

# Process multiple CSV files
trade_folder = 'data/input/trade_ledger'
print(f"\nProcessing trades from: {trade_folder}")

# Check if folder exists
if os.path.exists(trade_folder):
    files = [f for f in os.listdir(trade_folder) if f.startswith('trades_') and f.endswith('.csv')]
    print(f"✓ Found {len(files)} trade files: {sorted(files)}")
else:
    print(f"✗ Folder not found: {trade_folder}")
    sys.exit(1)

# Process the trades
try:
    trades_df = main_process_multiple_csvs(trade_folder, conn, close_prices)
    if trades_df is not None:
        print(f"✓ Processed {len(trades_df)} trades successfully")
    else:
        print("✗ No trades processed")
except Exception as e:
    print(f"✗ Error processing trades: {e}")
    import traceback
    traceback.print_exc()

# View results
try:
    daily_pos = view_daily_positions(conn)
    if not daily_pos.empty:
        print("\n✓ Daily positions calculated:")
        print(daily_pos[['date', 'method', 'open_position', 'closed_position', 'realized_pnl', 'unrealized_pnl']])
        
        # Summary by method
        for method in ['fifo', 'lifo']:
            method_data = daily_pos[daily_pos['method'] == method]
            if not method_data.empty:
                total_realized = method_data['realized_pnl'].sum()
                final_unrealized = method_data.iloc[-1]['unrealized_pnl']
                print(f"\n{method.upper()} Summary:")
                print(f"  Total Realized P&L: ${total_realized:.2f}")
                print(f"  Final Unrealized P&L: ${final_unrealized:.2f}")
                print(f"  Total P&L: ${total_realized + final_unrealized:.2f}")
    else:
        print("\n✗ No daily positions found")
except Exception as e:
    print(f"\n✗ Error viewing results: {e}")
    import traceback
    traceback.print_exc()

# Close database
conn.close()
print("\n✓ Test completed") 