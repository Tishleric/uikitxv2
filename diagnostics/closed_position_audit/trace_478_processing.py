"""
Trace how trade 20250804-478 was processed
"""
import sqlite3
import pandas as pd
from datetime import datetime

def trace_trade_478(db_path='../../trades.db'):
    """Trace the mystery trade 478"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("INVESTIGATING TRADE 20250804-478")
    print("=" * 80)
    
    # 1. Check if it exists in trades_fifo/lifo tables
    print("\n### 1. Looking for 20250804-478 in unrealized trades ###")
    
    for table in ['trades_fifo', 'trades_lifo']:
        query = f"""
        SELECT sequenceId, symbol, buySell, quantity, price, time
        FROM {table}
        WHERE sequenceId = '20250804-478'
        """
        result = conn.execute(query).fetchall()
        
        if result:
            print(f"\nFound in {table}:")
            for r in result:
                print(f"  SeqID: {r[0]}, Symbol: {r[1]}, Side: {r[2]}, Qty: {r[3]}, Price: {r[4]}")
        else:
            print(f"\nNot found in {table}")
    
    # 2. Check all realizations where it was the offsetting trade
    print("\n### 2. All realizations done by 20250804-478 ###")
    
    query = """
    SELECT DISTINCT
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.quantity,
        r.timestamp,
        -- Try to find the original symbol of the position being offset
        COALESCE(tf.symbol, tl.symbol) as original_position_symbol
    FROM realized_fifo r
    LEFT JOIN trades_fifo tf ON r.sequenceIdBeingOffset = tf.sequenceId
    LEFT JOIN trades_lifo tl ON r.sequenceIdBeingOffset = tl.sequenceId
    WHERE r.sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY r.timestamp
    """
    
    realizations = pd.read_sql_query(query, conn)
    
    print(f"\nTotal realizations: {len(realizations)}")
    if not realizations.empty:
        print("\nRealized trades:")
        print(realizations.to_string(index=False))
    
    # 3. Count unique symbols offset
    if not realizations.empty:
        unique_realized = realizations['realized_symbol'].unique()
        print(f"\n### 3. Unique symbols in realized trades: {len(unique_realized)} ###")
        for symbol in unique_realized:
            count = len(realizations[realizations['realized_symbol'] == symbol])
            print(f"  {symbol}: {count} realizations")
    
    # 4. Check processed files to see when 478 was processed
    print("\n### 4. When was trade 478 processed? ###")
    
    query = """
    SELECT file_path, processed_at, trade_count
    FROM processed_files
    WHERE file_path LIKE '%20250804%'
    ORDER BY processed_at
    """
    
    files = pd.read_sql_query(query, conn)
    if not files.empty:
        print("\nProcessed files for 2025-08-04:")
        print(files.to_string(index=False))
    
    # 5. Look for the actual trade in realized tables
    print("\n### 5. What trades were being offset? ###")
    
    # Get a sample of positions that were offset
    sample_positions = ['20250801-473', '20250801-474', '20250801-348']
    
    for pos_id in sample_positions:
        # Check what these positions were
        for table in ['trades_fifo', 'trades_lifo']:
            query = f"""
            SELECT sequenceId, symbol, buySell, quantity, price, time
            FROM {table}
            WHERE sequenceId = ?
            """
            result = conn.execute(query, (pos_id,)).fetchone()
            
            if result:
                print(f"\n{pos_id} in {table}:")
                print(f"  Symbol: {result[1]}, Side: {result[2]}, Qty: {result[3]}, Price: {result[4]}")
                break
        else:
            # Not in unrealized, check if we can reconstruct from realized
            query = """
            SELECT DISTINCT symbol, entryPrice
            FROM realized_fifo
            WHERE sequenceIdBeingOffset = ?
            LIMIT 1
            """
            result = conn.execute(query, (pos_id,)).fetchone()
            if result:
                print(f"\n{pos_id} (already fully realized):")
                print(f"  Symbol: {result[0]}, Entry Price: {result[1]}")
    
    # 6. Theory: Was 478 processed multiple times with different symbols?
    print("\n### 6. Checking for multiple processing patterns ###")
    
    query = """
    SELECT 
        symbol,
        MIN(timestamp) as first_realization,
        MAX(timestamp) as last_realization,
        COUNT(*) as realization_count
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    GROUP BY symbol
    ORDER BY MIN(timestamp)
    """
    
    patterns = pd.read_sql_query(query, conn)
    
    if not patterns.empty:
        print("\nRealization patterns by symbol:")
        print(patterns.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    trace_trade_478()