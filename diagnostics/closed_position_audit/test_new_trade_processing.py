"""
Test if NEW trades with various symbols offset correctly
This will help determine if the cross-symbol matching is an ongoing bug or historical artifact
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath('../..'))

from datetime import datetime
from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade

def test_new_trades(db_path='../../trades.db'):
    """Insert new test trades and verify they offset correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("TESTING NEW TRADE PROCESSING - MULTIPLE SYMBOLS")
    print("=" * 80)
    print(f"Test started: {datetime.now()}")
    
    # First, let's snapshot the current state
    print("\n### 1. CURRENT POSITION STATE ###")
    
    # Check existing positions by symbol
    query = """
    SELECT symbol, buySell, COUNT(*) as count, SUM(quantity) as total_qty
    FROM trades_fifo
    WHERE quantity > 0
    GROUP BY symbol, buySell
    ORDER BY symbol, buySell
    """
    
    positions = cursor.execute(query).fetchall()
    
    print("\nExisting positions in trades_fifo:")
    print(f"{'Symbol':<25} {'Side':<6} {'Count':<8} {'Total Qty'}")
    print("-" * 50)
    for pos in positions:
        print(f"{pos[0]:<25} {pos[1]:<6} {pos[2]:<8} {pos[3]:>10.1f}")
    
    # Count realized trades before test
    before_count = cursor.execute("SELECT COUNT(*) FROM realized_fifo").fetchone()[0]
    print(f"\nRealized trades before test: {before_count}")
    
    # Create test positions and trades
    print("\n### 2. INSERTING TEST POSITIONS ###")
    
    test_positions = [
        # Symbol, Side, Qty, Price, SeqId
        ('TEST_TYU5 Comdty', 'B', 10.0, 110.0, 'TEST-POS-001'),
        ('TEST_USU5 Comdty', 'B', 5.0, 115.0, 'TEST-POS-002'),
        ('TEST_OPTION Comdty', 'B', 20.0, 2.5, 'TEST-POS-003'),
    ]
    
    # Insert test positions
    for symbol, side, qty, price, seq_id in test_positions:
        cursor.execute(f"""
            INSERT INTO trades_fifo 
            (transactionId, symbol, price, original_price, quantity, buySell, 
             sequenceId, time, original_time, fullPartial)
            VALUES (99999, ?, ?, ?, ?, ?, ?, ?, ?, 'full')
        """, (symbol, price, price, qty, side, seq_id, 
              '2025-08-04 10:00:00.000', '2025-08-04 10:00:00.000'))
        print(f"  Inserted: {symbol} {side} {qty} @ {price}")
    
    conn.commit()
    
    # Now create offsetting trades
    print("\n### 3. PROCESSING OFFSETTING TRADES ###")
    
    test_trades = [
        # Test 1: TYU5 sell should ONLY offset TYU5 buy
        {
            'transactionId': 90001,
            'symbol': 'TEST_TYU5 Comdty',
            'price': 112.0,
            'quantity': 3.0,
            'buySell': 'S',
            'sequenceId': 'TEST-TRADE-001',
            'time': '2025-08-04 11:00:00.000',
            'fullPartial': 'full'
        },
        # Test 2: USU5 sell should ONLY offset USU5 buy
        {
            'transactionId': 90002,
            'symbol': 'TEST_USU5 Comdty',
            'price': 116.0,
            'quantity': 2.0,
            'buySell': 'S',
            'sequenceId': 'TEST-TRADE-002',
            'time': '2025-08-04 11:01:00.000',
            'fullPartial': 'full'
        },
        # Test 3: Option sell should ONLY offset option buy
        {
            'transactionId': 90003,
            'symbol': 'TEST_OPTION Comdty',
            'price': 2.8,
            'quantity': 10.0,
            'buySell': 'S',
            'sequenceId': 'TEST-TRADE-003',
            'time': '2025-08-04 11:02:00.000',
            'fullPartial': 'full'
        },
        # Test 4: Different USU5 sell - should NOT match TYU5!
        {
            'transactionId': 90004,
            'symbol': 'TEST_USU5 Comdty',
            'price': 116.5,
            'quantity': 1.0,
            'buySell': 'S',
            'sequenceId': 'TEST-TRADE-004',
            'time': '2025-08-04 11:03:00.000',
            'fullPartial': 'full'
        }
    ]
    
    # Process each test trade
    for trade in test_trades:
        print(f"\nProcessing: {trade['symbol']} {trade['buySell']} {trade['quantity']} @ {trade['price']}")
        
        # Call process_new_trade
        realized = process_new_trade(conn, trade, 'fifo')
        
        if realized:
            print(f"  Realized {len(realized)} trades:")
            for r in realized:
                print(f"    Offset {r['sequenceIdBeingOffset']} with {r['symbol']}")
                print(f"    Quantity: {r['quantity']}, P&L: {r['realizedPnL']}")
        else:
            print("  No realizations")
    
    conn.commit()
    
    # Check results
    print("\n### 4. VERIFICATION ###")
    
    # Check realized trades
    query = """
    SELECT 
        symbol,
        sequenceIdBeingOffset,
        sequenceIdDoingOffsetting,
        quantity,
        realizedPnL
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting LIKE 'TEST-TRADE-%'
    ORDER BY timestamp
    """
    
    realized = cursor.execute(query).fetchall()
    
    print("\nRealized trades from our test:")
    print(f"{'Symbol':<20} {'Being Offset':<15} {'Doing Offset':<15} {'Qty':<8} {'P&L'}")
    print("-" * 75)
    for r in realized:
        print(f"{r[0]:<20} {r[1]:<15} {r[2]:<15} {r[3]:<8.1f} {r[4]:>10.2f}")
    
    # Check for cross-symbol matching
    print("\n### 5. CROSS-SYMBOL CHECK ###")
    
    query = """
    SELECT COUNT(*) as cross_matches
    FROM realized_fifo r
    WHERE sequenceIdDoingOffsetting LIKE 'TEST-TRADE-%'
    AND (
        (r.symbol LIKE '%TYU5%' AND sequenceIdBeingOffset NOT LIKE '%TYU5%')
        OR
        (r.symbol LIKE '%USU5%' AND sequenceIdBeingOffset NOT LIKE '%USU5%')
        OR
        (r.symbol LIKE '%OPTION%' AND sequenceIdBeingOffset NOT LIKE '%OPTION%')
    )
    """
    
    cross_matches = cursor.execute(query).fetchone()[0]
    
    if cross_matches > 0:
        print(f"\n🚨 FOUND {cross_matches} CROSS-SYMBOL MATCHES! BUG IS STILL ACTIVE!")
    else:
        print("\n✅ No cross-symbol matches found. All trades offset correctly!")
    
    # Clean up test data
    print("\n### 6. CLEANUP ###")
    
    # Remove test trades
    cursor.execute("DELETE FROM trades_fifo WHERE sequenceId LIKE 'TEST-%'")
    cursor.execute("DELETE FROM trades_lifo WHERE sequenceId LIKE 'TEST-%'")
    cursor.execute("DELETE FROM realized_fifo WHERE sequenceIdDoingOffsetting LIKE 'TEST-TRADE-%'")
    cursor.execute("DELETE FROM realized_lifo WHERE sequenceIdDoingOffsetting LIKE 'TEST-TRADE-%'")
    
    conn.commit()
    print("Test data cleaned up")
    
    conn.close()
    print(f"\nTest completed: {datetime.now()}")


def check_watcher_state():
    """Check if watchers might be causing issues"""
    print("\n" + "=" * 80)
    print("CHECKING FOR WATCHER-RELATED ISSUES")
    print("=" * 80)
    
    # Check if trade_ledger_watcher is running
    print("\n### 1. Checking for multiple watcher processes ###")
    
    # Check processed_files table for patterns
    conn = sqlite3.connect('../../trades.db')
    
    query = """
    SELECT 
        file_path,
        COUNT(*) as process_count,
        MIN(processed_at) as first_processed,
        MAX(processed_at) as last_processed
    FROM processed_files
    WHERE file_path LIKE '%20250804%'
    GROUP BY file_path
    HAVING COUNT(*) > 1
    """
    
    multi_processed = conn.execute(query).fetchall()
    
    if multi_processed:
        print("\nFiles processed multiple times:")
        for file_path, count, first, last in multi_processed:
            print(f"  {file_path}: {count} times")
            print(f"    First: {first}, Last: {last}")
    else:
        print("\nNo files show multiple processing")
    
    # Check for rapid-fire processing
    query = """
    SELECT 
        DATE(timestamp) as date,
        sequenceIdDoingOffsetting,
        COUNT(*) as realization_count,
        COUNT(DISTINCT symbol) as unique_symbols
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    GROUP BY DATE(timestamp), sequenceIdDoingOffsetting
    """
    
    patterns = conn.execute(query).fetchall()
    
    print("\n### 2. Realization patterns for problematic trade 478 ###")
    for date, seq_id, count, symbols in patterns:
        print(f"  Date: {date}, Realizations: {count}, Unique symbols: {symbols}")
    
    conn.close()


if __name__ == "__main__":
    # Run the new trade test
    test_new_trades()
    
    # Check for watcher issues
    check_watcher_state()