"""
Check the specific offsetting trade that's causing duplicates
"""
import sqlite3
import pandas as pd
from datetime import datetime

def check_offsetting_trade(db_path='trades.db'):
    """Analyze the problematic offsetting trade 20250804-478"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("OFFSETTING TRADE ANALYSIS: 20250804-478")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Check if this trade exists in trades_fifo/lifo
    print("### Checking trades_fifo Table ###")
    
    # First, let's see the schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(trades_fifo)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Available columns: {columns}")
    
    # Check for the specific trade
    fifo_query = """
    SELECT *
    FROM trades_fifo
    WHERE sequenceId = '20250804-478'
       OR sequenceId = '20250801-474'
    """
    
    fifo_trades = pd.read_sql_query(fifo_query, conn)
    
    print(f"\nFound {len(fifo_trades)} trades in trades_fifo:")
    if len(fifo_trades) > 0:
        print(fifo_trades.to_string(index=False))
    
    # Check all trades from 2025-08-04
    print("\n### All trades from 2025-08-04 ###")
    
    today_trades = """
    SELECT 
        sequenceId,
        symbol,
        buySell,
        quantity,
        price,
        time
    FROM trades_fifo
    WHERE sequenceId LIKE '20250804-%'
    ORDER BY sequenceId
    """
    
    today = pd.read_sql_query(today_trades, conn)
    
    print(f"\nFound {len(today)} trades from 2025-08-04:")
    if len(today) > 0:
        print(today.to_string(index=False))
    
    # Check for any anomalies in quantity
    print("\n### Checking for Quantity Anomalies ###")
    
    quantity_check = """
    SELECT 
        symbol,
        buySell,
        COUNT(*) as trade_count,
        SUM(quantity) as total_quantity,
        MIN(quantity) as min_qty,
        MAX(quantity) as max_qty
    FROM trades_fifo
    WHERE quantity > 0
    GROUP BY symbol, buySell
    HAVING symbol IN ('USU5 Comdty', 'TYU5 Comdty')
    """
    
    qty_summary = pd.read_sql_query(quantity_check, conn)
    
    print("\nQuantity summary for affected symbols:")
    print(qty_summary.to_string(index=False))
    
    # Check if there are any trades with abnormally high quantities
    print("\n### Large Quantity Trades ###")
    
    large_trades = """
    SELECT 
        sequenceId,
        symbol,
        buySell,
        quantity,
        time
    FROM trades_fifo
    WHERE quantity > 100
    ORDER BY quantity DESC
    """
    
    large = pd.read_sql_query(large_trades, conn)
    
    if len(large) > 0:
        print("\nTrades with quantity > 100:")
        print(large.to_string(index=False))
    
    # Check the actual CSV file processing status
    print("\n### File Processing Status ###")
    
    # Check if processed_files table exists
    try:
        files_query = """
        SELECT 
            file_path,
            lines_processed,
            last_processed_time
        FROM processed_files
        WHERE last_processed_time >= datetime('now', '-2 days')
        ORDER BY last_processed_time DESC
        """
        files = pd.read_sql_query(files_query, conn)
        
        if len(files) > 0:
            print("\nRecently processed files:")
            print(files.to_string(index=False))
    except:
        print("\nprocessed_files table not found or has different schema")
    
    # Final check: are there multiple versions of the same trade?
    print("\n### Duplicate SequenceIds Check ###")
    
    duplicate_seq = """
    SELECT 
        sequenceId,
        COUNT(*) as count
    FROM trades_fifo
    GROUP BY sequenceId
    HAVING COUNT(*) > 1
    """
    
    dupes = pd.read_sql_query(duplicate_seq, conn)
    
    if len(dupes) > 0:
        print("\n⚠️ FOUND DUPLICATE SEQUENCE IDS!")
        print(dupes.to_string(index=False))
    else:
        print("\n✅ No duplicate sequence IDs found")
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_offsetting_trade()