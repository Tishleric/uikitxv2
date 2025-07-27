#!/usr/bin/env python3
"""
Test runner with forced output
"""
import sys
import os

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# Flush function
def print_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

print_flush("Starting P&L test...")
print_flush("Python version:", sys.version)
print_flush("Working directory:", os.getcwd())

try:
    # Import the module
    from lib.trading.pnl_fifo_lifo.main import process_multiple_csvs
    from lib.trading.pnl_fifo_lifo.data_manager import (
        create_all_tables, view_daily_positions
    )
    import sqlite3
    from datetime import datetime
    import pandas as pd
    
    print_flush("✓ Imports successful")
    
    # Historical prices
    close_prices = {
        datetime(2025, 7, 21).date(): 111.1875,
        datetime(2025, 7, 22).date(): 111.40625,
        datetime(2025, 7, 23).date(): 111.015625,
        datetime(2025, 7, 24).date(): 110.828125,
        datetime(2025, 7, 25).date(): 110.984375
    }
    
    # Check if database already exists
    db_exists = os.path.exists('trades.db')
    if db_exists:
        print_flush("\n! Database already exists, using existing data")
        conn = sqlite3.connect('trades.db')
    else:
        print_flush("\nCreating new database...")
        conn = sqlite3.connect('trades.db')
        create_all_tables(conn)
        
        # Process trades
        print_flush("\nProcessing trades from data/input/trade_ledger...")
        trades_df = process_multiple_csvs('data/input/trade_ledger', conn, close_prices)
        print_flush(f"✓ Processed {len(trades_df) if trades_df is not None else 0} trades")
    
    # View results
    print_flush("\nFetching results from database...")
    daily_pos = view_daily_positions(conn)
    
    if not daily_pos.empty:
        print_flush(f"\n✓ Found {len(daily_pos)} daily position records")
        print_flush("\nDaily Positions by Date and Method:")
        print_flush("="*80)
        
        # Display data
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print_flush(daily_pos[['date', 'method', 'open_position', 'closed_position', 
                              'realized_pnl', 'unrealized_pnl']].to_string())
        
        # Summary by method
        print_flush("\n" + "="*60)
        print_flush("FINAL SUMMARY BY METHOD:")
        print_flush("="*60)
        
        for method in ['fifo', 'lifo']:
            method_data = daily_pos[daily_pos['method'] == method]
            if not method_data.empty:
                total_realized = method_data['realized_pnl'].sum()
                final_unrealized = method_data.iloc[-1]['unrealized_pnl']
                total_pnl = total_realized + final_unrealized
                final_position = method_data.iloc[-1]['open_position']
                
                print_flush(f"\n{method.upper()} Method:")
                print_flush(f"  Days tracked: {len(method_data)}")
                print_flush(f"  Total Realized P&L: ${total_realized:,.2f}")
                print_flush(f"  Final Unrealized P&L: ${final_unrealized:,.2f}")
                print_flush(f"  Total P&L: ${total_pnl:,.2f}")
                print_flush(f"  Final Open Position: {final_position}")
    else:
        print_flush("\n! No daily positions found in database")
        
        # Check what's in the database
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print_flush("\nTables in database:", [t[0] for t in tables])
        
        for table in ['trades_fifo', 'trades_lifo', 'realized_fifo', 'realized_lifo']:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print_flush(f"  {table}: {count} records")
    
    conn.close()
    print_flush("\n✓ Test completed successfully!")
    
except Exception as e:
    print_flush(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

# Final flush
sys.stdout.flush()
print_flush("\nPress Enter to exit...")
input() 