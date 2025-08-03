"""
Test script to demonstrate dual tracking approach for daily closed positions.
This shows the current bug and the proposed fix side-by-side.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables, get_trading_day
from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    print("=== Testing Dual Tracking Approach ===\n")
    
    # Use temporary in-memory database
    conn = sqlite3.connect(':memory:')
    create_all_tables(conn)
    
    # Load trades from the complete file
    trade_file = 'data/input/trade_ledger/trades_20250801_complete.csv'
    if not os.path.exists(trade_file):
        # Fallback to regular file if complete doesn't exist
        trade_file = 'data/input/trade_ledger/trades_20250801.csv'
    
    print(f"Loading trades from: {trade_file}")
    trades_df = pd.read_csv(trade_file)
    
    # Translate symbols
    translator = RosettaStone()
    trades_df['bloomberg_symbol'] = trades_df['instrumentName'].apply(
        lambda x: translator.translate(x, 'actanttrades', 'bloomberg') if pd.notna(x) else x
    )
    
    # Parse timestamps and sort
    trades_df['marketTradeTime'] = pd.to_datetime(trades_df['marketTradeTime'])
    trades_df['trading_day'] = trades_df['marketTradeTime'].apply(get_trading_day)
    trades_df = trades_df.sort_values('marketTradeTime').reset_index(drop=True)
    
    # Filter for August 1st only
    aug1_trades = trades_df[trades_df['trading_day'] == datetime(2025, 8, 1).date()]
    print(f"Processing {len(aug1_trades)} trades for August 1st\n")
    
    # Initialize tracking dictionaries
    # Current method (aggregate - has the bug)
    daily_closed_aggregate = {'fifo': {'2025-08-01': {'quantity': 0, 'pnl': 0}}}
    
    # New method (per-symbol - the fix)
    daily_closed_per_symbol = {'fifo': {'2025-08-01': {}}}
    
    # Process each trade
    print("Processing trades and tracking closed positions...\n")
    
    for idx, row in aug1_trades.iterrows():
        trade = {
            'transactionId': row['tradeId'],
            'symbol': row['bloomberg_symbol'],
            'price': row['price'],
            'quantity': row['quantity'],
            'buySell': row['buySell'],
            'sequenceId': f"20250801-{idx+1}",
            'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        # Process with FIFO
        realized_trades = process_new_trade(conn, trade, 'fifo', 
                                          row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
        
        if realized_trades:
            realized_qty = sum(r['quantity'] for r in realized_trades)
            realized_pnl = sum(r['realizedPnL'] for r in realized_trades)
            
            # Current method (aggregate)
            daily_closed_aggregate['fifo']['2025-08-01']['quantity'] += realized_qty
            daily_closed_aggregate['fifo']['2025-08-01']['pnl'] += realized_pnl
            
            # New method (per-symbol)
            symbol = trade['symbol']
            if symbol not in daily_closed_per_symbol['fifo']['2025-08-01']:
                daily_closed_per_symbol['fifo']['2025-08-01'][symbol] = {'quantity': 0, 'pnl': 0}
            
            daily_closed_per_symbol['fifo']['2025-08-01'][symbol]['quantity'] += realized_qty
            daily_closed_per_symbol['fifo']['2025-08-01'][symbol]['pnl'] += realized_pnl
            
            # Show what would be stored in database
            print(f"\n{row['marketTradeTime'].strftime('%H:%M:%S')} - {symbol}: Closed {realized_qty} @ P&L ${realized_pnl:.2f}")
            print(f"  Current Method (BUG): Would store closed={daily_closed_aggregate['fifo']['2025-08-01']['quantity']}, pnl=${daily_closed_aggregate['fifo']['2025-08-01']['pnl']:.2f}")
            print(f"  Fixed Method: Would store closed={daily_closed_per_symbol['fifo']['2025-08-01'][symbol]['quantity']}, pnl=${daily_closed_per_symbol['fifo']['2025-08-01'][symbol]['pnl']:.2f}")
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL RESULTS FOR AUGUST 1ST")
    print("="*80)
    
    print("\nCURRENT METHOD (with bug) - What gets stored in daily_positions:")
    print("-" * 60)
    
    # Get unique symbols that had trades
    cursor = conn.cursor()
    symbols = cursor.execute("SELECT DISTINCT symbol FROM trades_fifo ORDER BY symbol").fetchall()
    
    for (symbol,) in symbols:
        # Count closed trades for this symbol
        closed_count = cursor.execute("""
            SELECT COUNT(*) FROM trades_fifo 
            WHERE symbol = ? AND quantity = 0
        """, (symbol,)).fetchone()[0]
        
        if closed_count > 0:
            # With the bug, every symbol gets the total aggregate
            print(f"{symbol:30} closed={daily_closed_aggregate['fifo']['2025-08-01']['quantity']:3}, "
                  f"pnl=${daily_closed_aggregate['fifo']['2025-08-01']['pnl']:10.2f} ❌")
    
    print("\nFIXED METHOD (per-symbol) - What should be stored:")
    print("-" * 60)
    
    for symbol, values in sorted(daily_closed_per_symbol['fifo']['2025-08-01'].items()):
        print(f"{symbol:30} closed={values['quantity']:3}, pnl=${values['pnl']:10.2f} ✓")
    
    # Show the specific options we care about
    print("\n" + "="*80)
    print("SPECIFIC OPTIONS COMPARISON:")
    print("="*80)
    
    options_of_interest = ['TYWQ25C1 112.5 Comdty', 'TYWQ25C1 112.75 Comdty']
    
    for opt in options_of_interest:
        if opt in daily_closed_per_symbol['fifo']['2025-08-01']:
            current_qty = daily_closed_aggregate['fifo']['2025-08-01']['quantity']
            current_pnl = daily_closed_aggregate['fifo']['2025-08-01']['pnl']
            
            fixed_qty = daily_closed_per_symbol['fifo']['2025-08-01'][opt]['quantity']
            fixed_pnl = daily_closed_per_symbol['fifo']['2025-08-01'][opt]['pnl']
            
            print(f"\n{opt}:")
            print(f"  Current: closed={current_qty} (WRONG), pnl=${current_pnl:.2f} (WRONG)")
            print(f"  Fixed:   closed={fixed_qty} (CORRECT), pnl=${fixed_pnl:.2f} (CORRECT)")
    
    conn.close()
    print("\n✅ Test complete - no changes made to trades.db or rebuild_historical_pnl.py")

if __name__ == '__main__':
    main()