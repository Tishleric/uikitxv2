"""
Self-contained diagnostic script to trace option closed position discrepancy.
Uses a temporary database and does not modify any production files.
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.trading.pnl_fifo_lifo import config
from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import (
    create_all_tables,
    view_unrealized_positions,
    get_trading_day,
    update_daily_position
)
from lib.trading.market_prices.rosetta_stone import RosettaStone

# Create a temporary database for testing
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db_path = temp_db.name
temp_db.close()

print(f"=== Option Position Diagnostic ===")
print(f"Using temporary database: {temp_db_path}")
print()

# Expected close prices for options
expected_close_prices = {
    'TYWQ25C1 112.25 Comdty': 0.234375,
    'TYWQ25C1 112.5 Comdty': 0.140625,
    'TYWQ25C1 112.75 Comdty': 0.078125,
    'TJWQ25C1 112.500 Comdty': 0.171875  # Check if this one is processed
}

try:
    # Load only August 1st trades
    trades_df = pd.read_csv('data/input/trade_ledger/trades_20250801.csv')
    
    # Filter for option trades only
    option_trades = trades_df[trades_df['instrumentName'].str.contains('XCMEO[CP]ADPS', regex=True)]
    
    print(f"Found {len(option_trades)} option trades in August 1st file")
    print("\n=== Option Trades Summary ===")
    
    # Group by instrument
    for instrument in sorted(option_trades['instrumentName'].unique()):
        trades = option_trades[option_trades['instrumentName'] == instrument]
        buys = trades[trades['buySell'] == 'B']
        sells = trades[trades['buySell'] == 'S']
        
        print(f"\n{instrument}:")
        print(f"  Total trades: {len(trades)}")
        print(f"  Buy quantity: {buys['quantity'].sum()}")
        print(f"  Sell quantity: {sells['quantity'].sum()}")
        print(f"  Net position: {buys['quantity'].sum() - sells['quantity'].sum()}")
    
    # Translate symbols
    print("\n=== Symbol Translation ===")
    translator = RosettaStone()
    
    # Track translated symbols
    translated_symbols = {}
    for instrument in option_trades['instrumentName'].unique():
        translated = translator.translate(instrument, 'actanttrades', 'bloomberg')
        translated_symbols[instrument] = translated
        print(f"{instrument} -> {translated}")
    
    # Check for missing option
    print("\n=== Checking for Missing Options ===")
    all_translated = set(translated_symbols.values())
    for expected_symbol in expected_close_prices.keys():
        if expected_symbol in all_translated:
            print(f"✓ {expected_symbol} found in trades")
        else:
            print(f"✗ {expected_symbol} NOT FOUND in trades")
    
    # Now process trades in temporary database
    conn = sqlite3.connect(temp_db_path)
    create_all_tables(conn)
    
    print("\n=== Processing Option Trades ===")
    
    # Process only option trades chronologically
    option_trades_sorted = option_trades.sort_values('marketTradeTime')
    
    # Track closed positions manually
    manual_closed_tracking = {
        'fifo': {},
        'lifo': {}
    }
    
    # Track every update to daily_positions
    daily_position_updates = []
    
    for idx, row in option_trades_sorted.iterrows():
        trade = {
            'transactionId': row['tradeId'],
            'symbol': translated_symbols[row['instrumentName']],
            'price': row['price'],
            'quantity': row['quantity'],
            'buySell': row['buySell'],
            'sequenceId': f"20250801-{idx+1}",
            'time': pd.to_datetime(row['marketTradeTime']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        print(f"\nProcessing: {trade['buySell']} {trade['quantity']} {trade['symbol']} @ {trade['price']}")
        
        for method in ['fifo', 'lifo']:
            # Process trade
            realized_trades = process_new_trade(conn, trade, method, 
                                              pd.to_datetime(row['marketTradeTime']).strftime('%Y-%m-%d %H:%M:%S'))
            
            if realized_trades:
                realized_qty = sum(r['quantity'] for r in realized_trades)
                print(f"  {method}: Realized {realized_qty} contracts")
                
                # Track manually
                symbol = trade['symbol']
                if symbol not in manual_closed_tracking[method]:
                    manual_closed_tracking[method][symbol] = 0
                manual_closed_tracking[method][symbol] += realized_qty
                
                # Record the update
                daily_position_updates.append({
                    'trade_id': trade['transactionId'],
                    'symbol': symbol,
                    'method': method,
                    'realized_qty': realized_qty,
                    'cumulative_closed': manual_closed_tracking[method][symbol]
                })
    
    print("\n=== Manual Closed Position Tracking ===")
    for method in ['fifo', 'lifo']:
        print(f"\n{method.upper()}:")
        for symbol, closed in manual_closed_tracking[method].items():
            print(f"  {symbol}: {closed} closed")
    
    # Query the database to see what was actually stored
    print("\n=== Database State Analysis ===")
    
    # Check trades tables
    for method in ['fifo', 'lifo']:
        print(f"\n{method.upper()} trades table:")
        query = f"""
            SELECT symbol, buySell, SUM(quantity) as total_qty, COUNT(*) as trade_count
            FROM trades_{method}
            WHERE symbol LIKE '%TYWQ25C1%' OR symbol LIKE '%TJWQ25C1%'
            GROUP BY symbol, buySell
            ORDER BY symbol, buySell
        """
        result = pd.read_sql_query(query, conn)
        print(result)
    
    # Check if update_daily_position was called
    print("\n=== Daily Position Updates Log ===")
    for update in daily_position_updates[-10:]:  # Show last 10 updates
        print(f"Trade {update['trade_id']}: {update['symbol']} {update['method']} "
              f"realized={update['realized_qty']}, cumulative={update['cumulative_closed']}")
    
    # Now simulate the EOD process to see final positions
    print("\n=== Simulating EOD Process ===")
    
    # Add some debug queries
    cursor = conn.cursor()
    
    # Check realized_trades table
    print("\n=== Realized Trades Table ===")
    realized_query = """
        SELECT method, symbol, SUM(quantity) as total_realized
        FROM realized_trades
        WHERE symbol LIKE '%TYWQ25C1%' OR symbol LIKE '%TJWQ25C1%'
        GROUP BY method, symbol
        ORDER BY symbol, method
    """
    realized_df = pd.read_sql_query(realized_query, conn)
    print(realized_df)
    
finally:
    # Clean up
    if 'conn' in locals():
        conn.close()
    os.unlink(temp_db_path)
    print(f"\nTemporary database cleaned up")