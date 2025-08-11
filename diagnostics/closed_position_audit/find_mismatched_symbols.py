"""
Find realized trades where the symbol doesn't match the original positions
This will prove the bug is happening in production
"""
import sqlite3
import pandas as pd
from datetime import datetime

def find_mismatched_symbols(db_path='trades.db'):
    """Find realized trades with mismatched symbols"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("FINDING REALIZED TRADES WITH MISMATCHED SYMBOLS")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # Query to find ALL realized trades and their original trades
    query = """
    WITH trade_symbols AS (
        -- Get symbols for all trades (both fifo and lifo)
        SELECT sequenceId, symbol FROM trades_fifo
        UNION ALL
        SELECT sequenceId, symbol FROM trades_lifo
        UNION ALL
        -- Also check historical trades that were fully realized
        SELECT DISTINCT sequenceIdBeingOffset as sequenceId, symbol 
        FROM realized_fifo
        UNION ALL
        SELECT DISTINCT sequenceIdDoingOffsetting as sequenceId, symbol
        FROM realized_fifo
    )
    SELECT 
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.sequenceIdDoingOffsetting,
        t1.symbol as original_position_symbol,
        t2.symbol as offsetting_trade_symbol,
        r.quantity,
        r.realizedPnL,
        DATE(r.timestamp) as date
    FROM realized_fifo r
    LEFT JOIN trade_symbols t1 ON r.sequenceIdBeingOffset = t1.sequenceId
    LEFT JOIN trade_symbols t2 ON r.sequenceIdDoingOffsetting = t2.sequenceId
    WHERE DATE(r.timestamp) >= DATE('now', '-7 days')
    ORDER BY r.timestamp DESC
    LIMIT 100
    """
    
    df = pd.read_sql_query(query, conn)
    
    if len(df) == 0:
        print("No realized trades found in the last 7 days")
        conn.close()
        return
    
    # Find mismatches
    print("### 1. Checking Symbol Consistency ###")
    print()
    
    # The bug: realized_symbol should match original_position_symbol, not offsetting_trade_symbol
    df['bug_present'] = df['realized_symbol'] == df['offsetting_trade_symbol']
    df['correct_recording'] = df['realized_symbol'] == df['original_position_symbol']
    
    bug_cases = df[df['bug_present'] & ~df['correct_recording']]
    
    if len(bug_cases) > 0:
        print(f"🐛 FOUND {len(bug_cases)} CASES OF THE BUG!")
        print("\nExamples where realized_symbol = offsetting_trade_symbol (WRONG):")
        print(bug_cases[['realized_symbol', 'original_position_symbol', 'offsetting_trade_symbol', 
                        'sequenceIdBeingOffset', 'sequenceIdDoingOffsetting']].head(10).to_string(index=False))
    else:
        print("✓ No obvious bug cases found")
    
    print("\n### 2. Symbol Recording Pattern ###")
    total = len(df)
    matches_offsetting = df['bug_present'].sum()
    matches_original = df['correct_recording'].sum()
    
    print(f"Total realized trades analyzed: {total}")
    print(f"Realized symbol = offsetting trade symbol: {matches_offsetting} ({matches_offsetting/total*100:.1f}%)")
    print(f"Realized symbol = original position symbol: {matches_original} ({matches_original/total*100:.1f}%)")
    
    # Look for cross-symbol realizations
    print("\n### 3. Cross-Symbol Realizations ###")
    cross_symbol = df[df['original_position_symbol'] != df['offsetting_trade_symbol']]
    
    if len(cross_symbol) > 0:
        print(f"\nFound {len(cross_symbol)} trades where different symbols were matched:")
        print(cross_symbol[['original_position_symbol', 'offsetting_trade_symbol', 'realized_symbol', 
                           'quantity', 'realizedPnL']].head(10).to_string(index=False))
    
    # Find specific problematic cases
    print("\n### 4. Specific Problem Cases ###")
    
    # Look for the known problematic trade
    problem_trades = df[df['sequenceIdDoingOffsetting'].isin(['20250804-478', '20250801-474'])]
    if len(problem_trades) > 0:
        print("\nKnown problematic trades:")
        print(problem_trades.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    find_mismatched_symbols('../../trades.db')