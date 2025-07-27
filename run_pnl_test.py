#!/usr/bin/env python3
"""
Run P&L test with trade ledger data
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and modify the test to use our data paths
from lib.trading.pnl_fifo_lifo import test_simulation

# First, let's create the combined samplestrades.csv that the test expects
# by combining all trade files
trade_files = sorted(Path('data/input/trade_ledger').glob('trades_*.csv'))
all_trades = []

for file in trade_files:
    df = pd.read_csv(file)
    all_trades.append(df)

if all_trades:
    combined_df = pd.concat(all_trades, ignore_index=True)
    combined_df.to_csv('samplestrades.csv', index=False)
    print(f"Created samplestrades.csv with {len(combined_df)} trades")

# Modify the test function to use our trade_ledger path
original_func = test_simulation.run_comprehensive_daily_breakdown

def modified_comprehensive_daily_breakdown():
    """Modified version that uses our trade_ledger path"""
    # Temporarily replace the hardcoded path in the function
    import sqlite3
    from datetime import datetime
    
    print("\n" + "="*20 + " COMPREHENSIVE DAILY P&L BREAKDOWN " + "="*20)
    
    # Historical close prices (from notebook)
    close_prices = {
        datetime(2025, 7, 21).date(): 111.1875,
        datetime(2025, 7, 22).date(): 111.40625,
        datetime(2025, 7, 23).date(): 111.015625,
        datetime(2025, 7, 24).date(): 110.828125,
        datetime(2025, 7, 25).date(): 110.984375
    }
    
    # Connect to database
    conn = sqlite3.connect('trades.db')
    
    # Create fresh tables
    print("\nCreating fresh database tables...")
    test_simulation.create_all_tables(conn)
    
    # Process multiple CSVs with daily tracking - using our path
    print("\nProcessing trades from data/input/trade_ledger folder...")
    trades_df = test_simulation.process_multiple_csvs('data/input/trade_ledger', conn, close_prices)
    
    if trades_df is None:
        print("ERROR: No trades loaded!")
        conn.close()
        return
    
    # Continue with the rest of the original function
    # Load the combined trades for display
    trades_csv = pd.read_csv('samplestrades.csv')
    trades_csv['marketTradeTime'] = pd.to_datetime(trades_csv['marketTradeTime'])
    trades_csv['trading_day'] = trades_csv['marketTradeTime'].apply(test_simulation.get_trading_day)
    trades_csv['date'] = trades_csv['trading_day']
    trades_csv = trades_csv.sort_values('marketTradeTime')
    
    # Generate sequence IDs
    trades_csv['date_str'] = trades_csv['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
    trades_csv['sequenceId'] = [f"{trades_csv.iloc[i]['date_str']}-{i+1}" for i in range(len(trades_csv))]
    
    # Get realized trades from database
    realized_trades = {}
    for method in ['fifo', 'lifo']:
        df = test_simulation.view_realized_trades(conn, method)
        if not df.empty:
            realized_trades[method] = df.set_index('sequenceIdDoingOffsetting')['realizedPnL'].to_dict()
    
    # Get daily position data
    daily_pos = test_simulation.view_daily_positions(conn)
    
    # Display results
    for method in ['fifo', 'lifo']:
        print(f"\n{'='*20} {method.upper()} Method {'='*20}")
        
        method_pos = daily_pos[daily_pos['method'] == method] if not daily_pos.empty else pd.DataFrame()
        
        if not method_pos.empty:
            print("\nDaily Summary:")
            print(method_pos[['date', 'open_position', 'closed_position', 'realized_pnl', 'unrealized_pnl']].to_string())
            
            # Calculate totals
            total_realized = method_pos['realized_pnl'].sum()
            final_unrealized = method_pos.iloc[-1]['unrealized_pnl'] if len(method_pos) > 0 else 0
            total_pnl = total_realized + final_unrealized
            
            print(f"\nTotal Realized P&L: ${total_realized:.2f}")
            print(f"Final Unrealized P&L: ${final_unrealized:.2f}")
            print(f"Total P&L: ${total_pnl:.2f}")
    
    conn.close()
    print("\n" + "="*60)

# Replace the function temporarily
test_simulation.run_comprehensive_daily_breakdown = modified_comprehensive_daily_breakdown

# Run the test
if __name__ == '__main__':
    print("Running P&L test with trade ledger data...")
    print("="*60)
    
    # Run only the comprehensive daily breakdown
    modified_comprehensive_daily_breakdown()
    
    # Clean up
    if os.path.exists('samplestrades.csv'):
        os.remove('samplestrades.csv')
        print("\nCleaned up temporary samplestrades.csv")
    
    if os.path.exists('trades.db'):
        print(f"\nDatabase created: trades.db ({os.path.getsize('trades.db')} bytes)") 