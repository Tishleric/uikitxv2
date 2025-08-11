"""
Trace exactly how trade 20250804-478 was processed to cause cross-symbol matching
"""
import sqlite3
import pandas as pd
from datetime import datetime

def trace_trade_processing(db_path='trades.db'):
    """Forensic trace of how a specific trade was processed"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("FORENSIC TRACE: TRADE 20250804-478 PROCESSING")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Step 1: What is the original trade?
    print("### Step 1: Original Trade Details ###")
    
    original_query = """
    SELECT 
        'fifo' as method,
        transactionId,
        symbol,
        price,
        quantity,
        buySell,
        sequenceId,
        time,
        fullPartial
    FROM trades_fifo
    WHERE sequenceId = '20250804-478'
    
    UNION ALL
    
    SELECT 
        'lifo' as method,
        transactionId,
        symbol,
        price,
        quantity,
        buySell,
        sequenceId,
        time,
        fullPartial
    FROM trades_lifo
    WHERE sequenceId = '20250804-478'
    """
    
    original = pd.read_sql_query(original_query, conn)
    print("\nOriginal trade in unrealized tables:")
    print(original.to_string(index=False))
    
    # Step 2: What trades did it offset?
    print("\n### Step 2: Trades It Offset (Should All Be TYU5 BUY) ###")
    
    offset_details = """
    SELECT 
        r.timestamp,
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.sequenceIdDoingOffsetting,
        r.quantity,
        r.entryPrice,
        r.exitPrice,
        -- Try to find the original trade being offset
        t.symbol as original_symbol,
        t.buySell as original_side
    FROM realized_fifo r
    LEFT JOIN trades_fifo t ON r.sequenceIdBeingOffset = t.sequenceId
    WHERE r.sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY r.timestamp
    """
    
    offsets = pd.read_sql_query(offset_details, conn)
    print(f"\nFound {len(offsets)} offset trades:")
    print(offsets.to_string(index=False))
    
    # Check for symbol mismatches
    mismatches = offsets[offsets['realized_symbol'] != 'TYU5 Comdty']
    if len(mismatches) > 0:
        print(f"\n⚠️ CRITICAL: {len(mismatches)} trades with WRONG SYMBOL!")
        print("These should all be TYU5 Comdty!")
    
    # Step 3: Check if the offset trades ever existed as different symbols
    print("\n### Step 3: Historical Check - Were These Ever TYU5? ###")
    
    # Check some of the problematic offset trades
    problem_trades = ['20250801-473', '20250801-474', '20250801-348']
    
    for trade_id in problem_trades:
        history_query = f"""
        -- Check if this trade ever existed in any table
        SELECT 
            'trades_fifo_current' as source,
            sequenceId,
            symbol,
            buySell,
            quantity
        FROM trades_fifo
        WHERE sequenceId = '{trade_id}'
        
        UNION ALL
        
        SELECT 
            'trades_lifo_current' as source,
            sequenceId,
            symbol,
            buySell,
            quantity
        FROM trades_lifo
        WHERE sequenceId = '{trade_id}'
        
        UNION ALL
        
        -- Check realized trades to see what symbol was recorded
        SELECT DISTINCT
            'realized_as_offset' as source,
            sequenceIdBeingOffset as sequenceId,
            symbol,
            'offset' as buySell,
            SUM(quantity) as quantity
        FROM realized_fifo
        WHERE sequenceIdBeingOffset = '{trade_id}'
        GROUP BY symbol
        """
        
        history = pd.read_sql_query(history_query, conn)
        
        print(f"\nHistory for trade {trade_id}:")
        if len(history) > 0:
            print(history.to_string(index=False))
        else:
            print("  Not found in any table")
    
    # Step 4: When did these realizations happen?
    print("\n### Step 4: Timing Analysis ###")
    
    timing_query = """
    SELECT 
        strftime('%Y-%m-%d %H:%M', timestamp) as time,
        symbol,
        sequenceIdBeingOffset,
        quantity,
        exitPrice
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY timestamp
    """
    
    timing = pd.read_sql_query(timing_query, conn)
    print("\nRealization timeline:")
    print(timing.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    trace_trade_processing()