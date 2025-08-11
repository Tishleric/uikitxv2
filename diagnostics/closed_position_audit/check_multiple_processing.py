"""
Check if trades are being processed multiple times or with changing symbols
"""
import sqlite3
import pandas as pd
from datetime import datetime

def check_multiple_processing(db_path='../../trades.db'):
    """Check for evidence of multiple processing"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("CHECKING FOR MULTIPLE PROCESSING OR SYMBOL CHANGES")
    print("=" * 80)
    
    # 1. Check if any sequenceId appears in both FIFO and LIFO with different symbols
    print("\n### 1. Checking for symbol mismatches between FIFO and LIFO ###")
    
    query = """
    SELECT 
        f.sequenceId,
        f.symbol as fifo_symbol,
        l.symbol as lifo_symbol
    FROM trades_fifo f
    JOIN trades_lifo l ON f.sequenceId = l.sequenceId
    WHERE f.symbol != l.symbol
    """
    
    mismatches = pd.read_sql_query(query, conn)
    
    if not mismatches.empty:
        print(f"\nFound {len(mismatches)} trades with different symbols in FIFO vs LIFO!")
        print(mismatches.head(20).to_string(index=False))
    else:
        print("\nNo symbol mismatches between FIFO and LIFO")
    
    # 2. Check realized trades for impossible scenarios
    print("\n### 2. Checking for impossible realized trades ###")
    
    # Find realized trades where the symbols don't match what we'd expect
    query = """
    WITH trade_info AS (
        -- Get all trades from both tables
        SELECT sequenceId, symbol, buySell FROM trades_fifo
        UNION ALL
        SELECT sequenceId, symbol, buySell FROM trades_lifo
    )
    SELECT 
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.sequenceIdDoingOffsetting,
        t1.symbol as offset_trade_symbol,
        t2.symbol as offsetting_trade_symbol,
        t1.buySell as offset_side,
        t2.buySell as offsetting_side
    FROM realized_fifo r
    LEFT JOIN trade_info t1 ON r.sequenceIdBeingOffset = t1.sequenceId
    LEFT JOIN trade_info t2 ON r.sequenceIdDoingOffsetting = t2.sequenceId
    WHERE 
        -- Look for cases where the offsetting trade has a different symbol
        (t2.symbol IS NOT NULL AND t2.symbol != r.symbol)
        OR
        -- Or where sides don't oppose each other
        (t1.buySell = t2.buySell AND t1.buySell IS NOT NULL AND t2.buySell IS NOT NULL)
    ORDER BY r.timestamp DESC
    LIMIT 50
    """
    
    impossible = pd.read_sql_query(query, conn)
    
    if not impossible.empty:
        print(f"\nFound {len(impossible)} impossible realized trades!")
        print("\nExamples:")
        print(impossible.head(20).to_string(index=False))
    
    # 3. Check if the same trade was inserted multiple times
    print("\n### 3. Checking for duplicate trade insertions ###")
    
    for table in ['trades_fifo', 'trades_lifo']:
        query = f"""
        SELECT 
            sequenceId,
            COUNT(*) as count,
            GROUP_CONCAT(DISTINCT symbol) as symbols,
            GROUP_CONCAT(DISTINCT price) as prices
        FROM {table}
        GROUP BY sequenceId
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """
        
        duplicates = pd.read_sql_query(query, conn)
        
        if not duplicates.empty:
            print(f"\n### Duplicate sequenceIds in {table}: ###")
            print(duplicates.to_string(index=False))
    
    # 4. Look at the trade ledger CSV to see what 478 actually was
    print("\n### 4. Checking trade ledger for original trade data ###")
    
    # First, let's see if we can find the actual CSV data
    csv_path = "../../data/input/trade_ledger/trades_20250804.csv"
    try:
        df = pd.read_csv(csv_path)
        
        # Find row 478 (assuming sequenceId is based on row number)
        if len(df) >= 478:
            trade_478 = df.iloc[477]  # 0-based index
            print(f"\nTrade #478 from CSV:")
            print(f"  tradeId: {trade_478.get('tradeId', 'N/A')}")
            print(f"  instrumentName: {trade_478.get('instrumentName', 'N/A')}")
            print(f"  buySell: {trade_478.get('buySell', 'N/A')}")
            print(f"  quantity: {trade_478.get('quantity', 'N/A')}")
            print(f"  price: {trade_478.get('price', 'N/A')}")
            print(f"  marketTradeTime: {trade_478.get('marketTradeTime', 'N/A')}")
    except Exception as e:
        print(f"\nCould not read trade ledger CSV: {e}")
    
    # 5. Theory: Check if symbol translation is causing issues
    print("\n### 5. Checking for symbol translation patterns ###")
    
    # Look for trades where the realized symbol doesn't match expected pattern
    query = """
    SELECT DISTINCT
        r.symbol,
        COUNT(DISTINCT r.sequenceIdDoingOffsetting) as unique_offsetting_trades,
        COUNT(*) as total_realizations
    FROM realized_fifo r
    WHERE DATE(r.timestamp) >= DATE('now', '-7 days')
    GROUP BY r.symbol
    ORDER BY COUNT(*) DESC
    """
    
    patterns = pd.read_sql_query(query, conn)
    
    print("\nRealization patterns by symbol:")
    print(patterns.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    check_multiple_processing()