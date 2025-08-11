"""
Find what's triggering the re-processing of already realized trades
"""
import sqlite3
import pandas as pd
from datetime import datetime

def find_reprocessing_trigger(db_path='trades.db'):
    """Find evidence of what's re-processing trades"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("REPROCESSING TRIGGER INVESTIGATION")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Key insight: Check if there are any processes that might be re-loading
    # and re-processing CSV files or trades
    
    # First, let's check if the problematic trades still exist in trades_fifo
    print("### Status of Already-Realized Trades ###")
    
    # Get all the trades that were supposedly offset by 20250804-478
    offset_trades_query = """
    SELECT DISTINCT sequenceIdBeingOffset
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    """
    
    offset_trades = pd.read_sql_query(offset_trades_query, conn)
    
    print(f"\nTrades that were offset by 20250804-478:")
    print(offset_trades['sequenceIdBeingOffset'].tolist())
    
    # Now check if these trades still exist in trades_fifo
    if len(offset_trades) > 0:
        trade_ids = "','".join(offset_trades['sequenceIdBeingOffset'].tolist())
        check_query = f"""
        SELECT sequenceId, symbol, quantity, buySell
        FROM trades_fifo
        WHERE sequenceId IN ('{trade_ids}')
        """
        
        still_exist = pd.read_sql_query(check_query, conn)
        
        if len(still_exist) > 0:
            print(f"\n⚠️ WARNING: {len(still_exist)} already-realized trades STILL EXIST in trades_fifo!")
            print("This means they could be matched again!")
            print(still_exist.to_string(index=False))
        else:
            print("\n✅ Good: None of the realized trades exist in trades_fifo anymore")
    
    # Check if close price updates correlate with duplicate realizations
    print("\n### Close Price Update Correlation ###")
    
    close_price_updates = """
    SELECT 
        symbol,
        price,
        timestamp,
        strftime('%H:%M', timestamp) as update_time
    FROM pricing
    WHERE price_type = 'close'
      AND DATE(timestamp) >= '2025-08-03'
    ORDER BY timestamp DESC
    LIMIT 20
    """
    
    close_prices = pd.read_sql_query(close_price_updates, conn)
    
    print("\nRecent close price updates:")
    print(close_prices[['update_time', 'symbol', 'price']].to_string(index=False))
    
    # Check for any scripts or processes that might be re-running
    print("\n### Checking for Batch Processing Evidence ###")
    
    # Look for large bursts of realizations
    burst_check = """
    SELECT 
        strftime('%Y-%m-%d %H:%M', timestamp) as minute,
        COUNT(*) as realizations,
        COUNT(DISTINCT sequenceIdDoingOffsetting) as unique_offsetting,
        COUNT(DISTINCT sequenceIdBeingOffset) as unique_offset
    FROM realized_fifo
    WHERE timestamp >= datetime('now', '-1 day')
    GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
    HAVING COUNT(*) > 10
    ORDER BY realizations DESC
    """
    
    bursts = pd.read_sql_query(burst_check, conn)
    
    if len(bursts) > 0:
        print("\nFound realization bursts (>10 per minute):")
        print(bursts.to_string(index=False))
    
    # Final check: Look for any pattern in how trades are being inserted
    print("\n### Trade Insertion Pattern ###")
    
    insertion_pattern = """
    SELECT 
        DATE(original_time) as trade_date,
        COUNT(*) as trade_count,
        MIN(time) as earliest_process_time,
        MAX(time) as latest_process_time,
        COUNT(DISTINCT time) as unique_process_times
    FROM trades_fifo
    WHERE DATE(original_time) >= '2025-08-01'
    GROUP BY DATE(original_time)
    HAVING unique_process_times > 1
    """
    
    patterns = pd.read_sql_query(insertion_pattern, conn)
    
    if len(patterns) > 0:
        print("\nTrades processed at multiple different times:")
        print(patterns.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    find_reprocessing_trigger()