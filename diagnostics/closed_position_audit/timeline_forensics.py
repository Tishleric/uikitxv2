"""
Forensic analysis of what happened during the duplication window
"""
import sqlite3
import pandas as pd
from datetime import datetime

def timeline_forensics(db_path='trades.db'):
    """Analyze exactly what happened during the duplication window (5:00-6:30 AM)"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("FORENSIC TIMELINE ANALYSIS")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Get ALL database activity during the critical window
    print("### All Realized Trades During Critical Window (5:00-6:30 AM on 2025-08-04) ###")
    
    window_query = """
    SELECT 
        strftime('%H:%M:%S', timestamp) as time,
        symbol,
        sequenceIdBeingOffset || ' -> ' || sequenceIdDoingOffsetting as trade_pair,
        quantity,
        exitPrice,
        realizedPnL
    FROM realized_fifo
    WHERE timestamp >= '2025-08-04 05:00:00' 
      AND timestamp <= '2025-08-04 06:30:00'
    ORDER BY timestamp
    """
    
    window_activity = pd.read_sql_query(window_query, conn)
    
    print(f"\nFound {len(window_activity)} trades realized during this window:")
    if len(window_activity) > 0:
        # Group by symbol to see pattern
        symbol_summary = window_activity.groupby('symbol').agg({
            'quantity': ['count', 'sum'],
            'realizedPnL': 'sum'
        })
        print("\nSummary by symbol:")
        print(symbol_summary)
        
        # Show first 20 trades
        print("\nFirst 20 trades in window:")
        print(window_activity.head(20).to_string(index=False))
    
    # Check if these correlate with specific offsetting trades
    print("\n### Unique Offsetting Trades ###")
    
    offsetting_query = """
    SELECT 
        sequenceIdDoingOffsetting as offsetting_id,
        COUNT(*) as times_used,
        GROUP_CONCAT(DISTINCT sequenceIdBeingOffset) as offset_trades,
        SUM(quantity) as total_quantity
    FROM realized_fifo
    WHERE timestamp >= '2025-08-04 05:00:00' 
      AND timestamp <= '2025-08-04 06:30:00'
    GROUP BY sequenceIdDoingOffsetting
    HAVING COUNT(*) > 1
    ORDER BY times_used DESC
    """
    
    offsetting = pd.read_sql_query(offsetting_query, conn)
    
    if len(offsetting) > 0:
        print("\nOffsetting trades used multiple times:")
        print(offsetting.to_string(index=False))
    
    # Check what happened just before the duplication window
    print("\n### Activity Before Duplication Window (4:00-5:00 AM) ###")
    
    before_query = """
    SELECT 
        strftime('%H:%M:%S', timestamp) as time,
        'realized_' || method as table_name,
        COUNT(*) as trades_count
    FROM (
        SELECT timestamp, 'fifo' as method FROM realized_fifo 
        WHERE timestamp >= '2025-08-04 04:00:00' AND timestamp < '2025-08-04 05:00:00'
        UNION ALL
        SELECT timestamp, 'lifo' as method FROM realized_lifo 
        WHERE timestamp >= '2025-08-04 04:00:00' AND timestamp < '2025-08-04 05:00:00'
    )
    GROUP BY strftime('%Y-%m-%d %H:%M', timestamp), method
    ORDER BY timestamp
    """
    
    before_activity = pd.read_sql_query(before_query, conn)
    
    if len(before_activity) > 0:
        print("\nActivity in hour before duplications:")
        print(before_activity.to_string(index=False))
    else:
        print("\nNo activity in the hour before duplications started")
    
    # Check daily_positions updates during this time
    print("\n### Daily Positions During Window ###")
    
    # Since daily_positions doesn't have timestamps, check the values
    daily_check = """
    SELECT 
        date,
        symbol,
        method,
        closed_position
    FROM daily_positions
    WHERE date = '2025-08-04'
      AND symbol IN ('USU5 Comdty', 'TYU5 Comdty')
    ORDER BY symbol, method
    """
    
    daily = pd.read_sql_query(daily_check, conn)
    
    print("\nDaily positions for 2025-08-04:")
    print(daily.to_string(index=False))
    
    # Look for any patterns in the sequence IDs
    print("\n### Sequence ID Pattern Analysis ###")
    
    sequence_pattern = """
    SELECT 
        SUBSTR(sequenceIdDoingOffsetting, 1, 10) as offset_date,
        COUNT(*) as realization_count,
        COUNT(DISTINCT sequenceIdBeingOffset) as unique_offset_trades
    FROM realized_fifo
    WHERE timestamp >= '2025-08-04 05:00:00' 
      AND timestamp <= '2025-08-04 06:30:00'
    GROUP BY SUBSTR(sequenceIdDoingOffsetting, 1, 10)
    """
    
    patterns = pd.read_sql_query(sequence_pattern, conn)
    
    print("\nOffsetting trade date patterns:")
    print(patterns.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    timeline_forensics()