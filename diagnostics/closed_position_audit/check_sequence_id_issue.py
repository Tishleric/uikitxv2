"""
Check if duplicate sequence IDs are causing the cross-symbol matching issue
"""
import sqlite3
import pandas as pd
from datetime import datetime

def check_sequence_id_issue(db_path='trades.db'):
    """Check for duplicate sequence IDs that could cause cross-symbol matching"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("SEQUENCE ID DUPLICATION ANALYSIS")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Check if there are duplicate sequence IDs across different symbols
    print("### Checking for Duplicate Sequence IDs ###")
    
    duplicate_seq_query = """
    -- Check trades_fifo for duplicate sequenceIds with different symbols
    SELECT 
        sequenceId,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols,
        COUNT(*) as count
    FROM trades_fifo
    GROUP BY sequenceId
    HAVING COUNT(DISTINCT symbol) > 1
    """
    
    duplicates = pd.read_sql_query(duplicate_seq_query, conn)
    
    if len(duplicates) > 0:
        print("\n⚠️ CRITICAL: Found sequence IDs used for MULTIPLE SYMBOLS in trades_fifo!")
        print("This could cause cross-symbol matching!")
        print(duplicates.to_string(index=False))
    else:
        print("\n✅ No duplicate sequence IDs across symbols in trades_fifo")
    
    # Check realized tables for the pattern
    print("\n### Checking Realized Tables for Sequence ID Issues ###")
    
    realized_check = """
    -- Look for cases where the same sequenceId appears with different symbols
    SELECT 
        'realized_fifo' as table_name,
        sequenceIdDoingOffsetting,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols,
        COUNT(*) as times_used
    FROM realized_fifo
    WHERE DATE(timestamp) >= DATE('now', '-5 days')
    GROUP BY sequenceIdDoingOffsetting
    HAVING COUNT(DISTINCT symbol) > 1
    
    UNION ALL
    
    SELECT 
        'realized_lifo' as table_name,
        sequenceIdDoingOffsetting,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols,
        COUNT(*) as times_used
    FROM realized_lifo
    WHERE DATE(timestamp) >= DATE('now', '-5 days')
    GROUP BY sequenceIdDoingOffsetting
    HAVING COUNT(DISTINCT symbol) > 1
    """
    
    realized_issues = pd.read_sql_query(realized_check, conn)
    
    if len(realized_issues) > 0:
        print("\nOffsetting trades used for multiple symbols:")
        print(realized_issues.to_string(index=False))
    
    # Check the actual trades that are causing problems
    print("\n### Investigating Problem Trade 20250804-478 ###")
    
    # Check all tables for this sequence ID
    problem_query = """
    SELECT 'trades_fifo' as source, sequenceId, symbol, buySell, quantity, price
    FROM trades_fifo WHERE sequenceId = '20250804-478'
    
    UNION ALL
    
    SELECT 'trades_lifo' as source, sequenceId, symbol, buySell, quantity, price
    FROM trades_lifo WHERE sequenceId = '20250804-478'
    
    UNION ALL
    
    SELECT DISTINCT 'realized_fifo_offset' as source, sequenceIdBeingOffset as sequenceId, 
           symbol, 'offset' as buySell, SUM(quantity) as quantity, AVG(entryPrice) as price
    FROM realized_fifo 
    WHERE sequenceIdBeingOffset = '20250804-478'
    GROUP BY symbol
    
    UNION ALL
    
    SELECT DISTINCT 'realized_fifo_offsetting' as source, sequenceIdDoingOffsetting as sequenceId,
           symbol, 'offsetting' as buySell, SUM(quantity) as quantity, AVG(exitPrice) as price
    FROM realized_fifo 
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    GROUP BY symbol
    """
    
    problem_trades = pd.read_sql_query(problem_query, conn)
    
    print("\nAll occurrences of sequence ID 20250804-478:")
    print(problem_trades.to_string(index=False))
    
    # Check how sequence IDs are distributed
    print("\n### Sequence ID Generation Pattern ###")
    
    seq_pattern = """
    SELECT 
        SUBSTR(sequenceId, 1, 10) as date_part,
        MIN(CAST(SUBSTR(sequenceId, 12) as INTEGER)) as min_seq,
        MAX(CAST(SUBSTR(sequenceId, 12) as INTEGER)) as max_seq,
        COUNT(*) as trade_count
    FROM trades_fifo
    WHERE sequenceId LIKE '2025080%-%'
    GROUP BY SUBSTR(sequenceId, 1, 10)
    ORDER BY date_part DESC
    """
    
    seq_patterns = pd.read_sql_query(seq_pattern, conn)
    
    print("\nSequence ID patterns by date:")
    print(seq_patterns.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_sequence_id_issue()