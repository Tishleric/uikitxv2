"""
Deep investigation of the cross-symbol matching bug
"""
import sqlite3
import pandas as pd
from datetime import datetime

def investigate_symbol_bug(db_path='../../trades.db'):
    """Investigate why cross-symbol matching is happening"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("CROSS-SYMBOL MATCHING BUG INVESTIGATION")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    # First, let's look at the specific problematic trades
    print("### Investigating Trade 20250804-478 (TYU5) ###")
    
    # Check trades_fifo for this trade
    query1 = """
    SELECT * FROM trades_fifo 
    WHERE sequenceId = '20250804-478'
    """
    
    trade_478 = pd.read_sql_query(query1, conn)
    print("\nTrade 20250804-478 in trades_fifo:")
    if len(trade_478) > 0:
        print(trade_478.to_string(index=False))
    else:
        print("NOT FOUND in trades_fifo (may have been fully offset)")
    
    # Check what this trade has offset
    print("\n### What Trade 20250804-478 Has Offset ###")
    
    offset_query = """
    SELECT 
        symbol,
        sequenceIdBeingOffset,
        quantity,
        entryPrice,
        exitPrice,
        realizedPnL,
        timestamp
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    ORDER BY timestamp
    """
    
    offsets = pd.read_sql_query(offset_query, conn)
    print(f"\nFound {len(offsets)} trades offset by 20250804-478:")
    if len(offsets) > 0:
        print(offsets.to_string(index=False))
        
        # Check unique symbols
        unique_symbols = offsets['symbol'].unique()
        print(f"\nUnique symbols in realized trades: {unique_symbols}")
        
        if len(unique_symbols) > 1:
            print("\n⚠️ CRITICAL: Same offsetting trade used for MULTIPLE SYMBOLS!")
    
    # Now check the trades that were offset - do they exist in trades_fifo?
    print("\n### Checking Offset Trades Original Symbols ###")
    
    if len(offsets) > 0:
        offset_ids = offsets['sequenceIdBeingOffset'].unique()
        for trade_id in offset_ids[:3]:  # Check first 3
            check_query = f"""
            SELECT sequenceId, symbol, buySell, quantity, price
            FROM trades_fifo
            WHERE sequenceId = '{trade_id}'
            
            UNION ALL
            
            SELECT sequenceId, symbol, buySell, quantity, price
            FROM trades_lifo
            WHERE sequenceId = '{trade_id}'
            """
            
            original = pd.read_sql_query(check_query, conn)
            
            print(f"\nOriginal trade {trade_id}:")
            if len(original) > 0:
                print(f"  Still exists with symbol: {original['symbol'].iloc[0]}")
            else:
                print(f"  Not found (properly removed)")
    
    # Check if there's a pattern in recent realized trades
    print("\n### Recent Realized Trades Pattern ###")
    
    pattern_query = """
    SELECT 
        DATE(timestamp) as date,
        sequenceIdDoingOffsetting,
        COUNT(DISTINCT symbol) as unique_symbols,
        GROUP_CONCAT(DISTINCT symbol) as symbols_list,
        COUNT(*) as offset_count
    FROM realized_fifo
    WHERE DATE(timestamp) >= DATE('now', '-2 days')
    GROUP BY DATE(timestamp), sequenceIdDoingOffsetting
    HAVING unique_symbols > 1
    ORDER BY date DESC, offset_count DESC
    """
    
    patterns = pd.read_sql_query(pattern_query, conn)
    
    if len(patterns) > 0:
        print("\n⚠️ Offsetting trades used for multiple symbols:")
        print(patterns.to_string(index=False))
    
    # Check the actual matching process - look for any trades with wrong symbols
    print("\n### Symbol Storage Check ###")
    
    symbol_check = """
    SELECT 
        'trades_fifo' as table_name,
        symbol,
        COUNT(*) as count
    FROM trades_fifo
    GROUP BY symbol
    
    UNION ALL
    
    SELECT 
        'realized_fifo' as table_name,
        symbol,
        COUNT(*) as count
    FROM realized_fifo
    WHERE DATE(timestamp) >= DATE('now', '-5 days')
    GROUP BY symbol
    ORDER BY table_name, symbol
    """
    
    symbols = pd.read_sql_query(symbol_check, conn)
    print("\nSymbols in database:")
    print(symbols.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    investigate_symbol_bug()