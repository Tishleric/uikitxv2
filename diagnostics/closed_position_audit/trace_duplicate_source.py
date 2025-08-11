"""
Trace the source of duplicate trade insertions
Focus on the specific trades that are duplicated
"""
import sqlite3
import pandas as pd
from datetime import datetime

def trace_duplicate_source(db_path='trades.db'):
    """Deep dive into specific duplicate trades to understand their source"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("DUPLICATE TRADE SOURCE ANALYSIS")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Focus on the most duplicated trade: 20250801-474 -> 20250804-478
    print("### Analyzing Most Duplicated Trade: 20250801-474 -> 20250804-478 ###\n")
    
    # Get all instances of this trade from realized_fifo
    query = """
    SELECT 
        *,
        datetime(timestamp) as formatted_time
    FROM realized_fifo
    WHERE sequenceIdBeingOffset = '20250801-474' 
      AND sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY timestamp
    """
    
    duplicates = pd.read_sql_query(query, conn)
    
    print(f"Found {len(duplicates)} instances of this trade:")
    print("-" * 120)
    
    if len(duplicates) > 0:
        # Show all columns to understand differences
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(duplicates[['formatted_time', 'symbol', 'quantity', 'entryPrice', 
                         'exitPrice', 'realizedPnL']].to_string(index=False))
        
        # Check time intervals between duplicates
        print("\nTime intervals between duplicate insertions:")
        times = pd.to_datetime(duplicates['timestamp'])
        for i in range(1, len(times)):
            interval = times.iloc[i] - times.iloc[i-1]
            print(f"  Entry {i} to {i+1}: {interval}")
    
    # Check if trades_fifo has duplicates (the source table)
    print("\n### Checking trades_fifo table for source duplicates ###")
    
    trades_query = """
    SELECT 
        sequenceId,
        COUNT(*) as count
    FROM trades_fifo
    WHERE sequenceId IN ('20250801-474', '20250804-478')
    GROUP BY sequenceId
    """
    
    trade_counts = pd.read_sql_query(trades_query, conn)
    print("\nTrade counts in trades_fifo:")
    print(trade_counts)
    
    # Check all trades from recent problematic period
    print("\n### Recent Trade Processing Pattern ###")
    
    recent_pattern = """
    SELECT 
        DATE(timestamp) as trade_date,
        strftime('%H', timestamp) as hour,
        symbol,
        COUNT(*) as trades_processed,
        SUM(quantity) as total_quantity
    FROM realized_fifo
    WHERE DATE(timestamp) >= '2025-08-03'
    GROUP BY DATE(timestamp), strftime('%H', timestamp), symbol
    ORDER BY trade_date DESC, hour DESC, symbol
    """
    
    pattern = pd.read_sql_query(recent_pattern, conn)
    
    print("\nHourly trade processing pattern (last 2 days):")
    print(pattern[pattern['trades_processed'] > 10])  # Show hours with high activity
    
    # Check if there's a correlation with specific hours (maybe a watcher restart?)
    print("\n### Checking for Processing Bursts ###")
    
    burst_query = """
    SELECT 
        strftime('%Y-%m-%d %H:%M', timestamp) as minute,
        COUNT(*) as trades_in_minute,
        GROUP_CONCAT(DISTINCT symbol) as symbols
    FROM realized_fifo
    WHERE DATE(timestamp) >= '2025-08-03'
    GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
    HAVING COUNT(*) > 5
    ORDER BY trades_in_minute DESC
    LIMIT 20
    """
    
    bursts = pd.read_sql_query(burst_query, conn)
    
    if len(bursts) > 0:
        print("\nProcessing bursts (>5 trades per minute):")
        print(bursts.to_string(index=False))
    
    # Check daily_positions updates for the affected symbols
    print("\n### Daily Positions Update Pattern ###")
    
    daily_updates = """
    SELECT 
        date,
        symbol,
        method,
        closed_position,
        LAG(closed_position, 1, 0) OVER (PARTITION BY symbol, method ORDER BY date) as prev_closed,
        closed_position - LAG(closed_position, 1, 0) OVER (PARTITION BY symbol, method ORDER BY date) as daily_change
    FROM daily_positions
    WHERE symbol IN ('TYU5 Comdty', 'USU5 Comdty')
      AND date >= '2025-08-01'
    ORDER BY symbol, date
    """
    
    daily = pd.read_sql_query(daily_updates, conn)
    
    print("\nDaily position changes for affected symbols:")
    print(daily.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    trace_duplicate_source()