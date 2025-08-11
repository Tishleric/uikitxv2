"""
Proof of concept to demonstrate the symbol storage bug in realized trades
"""
import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

# Add the pnl module to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def create_test_database():
    """Create a test database to demonstrate the bug"""
    conn = sqlite3.connect(':memory:')  # In-memory database for testing
    cursor = conn.cursor()
    
    # Create minimal schema
    cursor.execute("""
    CREATE TABLE trades_fifo (
        transactionId TEXT,
        symbol TEXT,
        price REAL,
        original_price REAL,
        quantity REAL,
        buySell TEXT,
        sequenceId TEXT PRIMARY KEY,
        time TEXT,
        original_time TEXT,
        fullPartial TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE realized_fifo (
        symbol TEXT,
        sequenceIdBeingOffset TEXT,
        sequenceIdDoingOffsetting TEXT,
        partialFull TEXT,
        quantity REAL,
        entryPrice REAL,
        exitPrice REAL,
        realizedPnL REAL,
        timestamp TEXT
    )
    """)
    
    # Insert test trades - USU5 BUY positions
    cursor.execute("""
    INSERT INTO trades_fifo VALUES 
    ('TEST-1', 'USU5 Comdty', 115.50, 115.50, 5.0, 'B', 'TEST-001', 
     '2025-08-04 10:00:00.000', '2025-08-04 10:00:00.000', 'full')
    """)
    
    conn.commit()
    return conn

def test_current_behavior(conn):
    """Test what happens with current code behavior"""
    print("=" * 80)
    print("TESTING CURRENT BEHAVIOR")
    print("=" * 80)
    
    from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
    
    # Create a TYU5 SELL trade to offset the USU5 position
    offsetting_trade = {
        'transactionId': 'TEST-2',
        'symbol': 'TYU5 Comdty',  # Different symbol!
        'price': 112.50,
        'quantity': 3.0,
        'buySell': 'S',
        'sequenceId': 'TEST-002',
        'time': '2025-08-04 11:00:00.000',
        'fullPartial': 'full'
    }
    
    print("\n1. Initial state:")
    print("   USU5 BUY position exists (5 contracts)")
    print("   Incoming: TYU5 SELL trade (3 contracts)")
    print("   These should NOT match (different symbols)")
    
    # Process the trade
    print("\n2. Processing TYU5 SELL trade...")
    realized = process_new_trade(conn, offsetting_trade, 'fifo')
    
    # Check what happened
    cursor = conn.cursor()
    
    # Check realized trades
    realized_df = pd.read_sql_query("SELECT * FROM realized_fifo", conn)
    print("\n3. Realized trades created:")
    if len(realized_df) > 0:
        print(realized_df[['symbol', 'sequenceIdBeingOffset', 'sequenceIdDoingOffsetting', 'quantity']].to_string(index=False))
        
        # Check which symbol was stored
        stored_symbol = realized_df['symbol'].iloc[0]
        print(f"\n   ⚠️ Stored symbol: {stored_symbol}")
        print(f"   Should be: USU5 Comdty (the original position)")
        print(f"   Actually stored: {stored_symbol} (the offsetting trade)")
    else:
        print("   No realized trades (as expected - different symbols)")
    
    # Check remaining positions
    positions_df = pd.read_sql_query("SELECT * FROM trades_fifo", conn)
    print("\n4. Remaining positions:")
    print(positions_df[['symbol', 'buySell', 'quantity', 'sequenceId']].to_string(index=False))
    
    return realized_df

def test_symbol_matching_logic(conn):
    """Test the SQL query that should prevent cross-symbol matching"""
    print("\n" + "=" * 80)
    print("TESTING SYMBOL MATCHING LOGIC")
    print("=" * 80)
    
    cursor = conn.cursor()
    
    # The query from process_new_trade
    positions_query = """
        SELECT sequenceId, transactionId, symbol, price, quantity, time 
        FROM trades_fifo 
        WHERE symbol = ? AND buySell = ? AND quantity > 0
        ORDER BY sequenceId ASC
    """
    
    # Test 1: Correct symbol
    print("\n1. Query with matching symbol (TYU5 looking for TYU5 longs):")
    result1 = cursor.execute(positions_query, ('TYU5 Comdty', 'B')).fetchall()
    print(f"   Found {len(result1)} positions")
    
    # Test 2: Different symbol  
    print("\n2. Query with different symbol (TYU5 looking for USU5 longs):")
    result2 = cursor.execute(positions_query, ('USU5 Comdty', 'B')).fetchall()
    print(f"   Found {len(result2)} positions")
    for r in result2:
        print(f"   - {r[2]} (seq: {r[0]})")
    
    # Test 3: What the query actually sees
    print("\n3. What symbols are in trades_fifo:")
    all_symbols = cursor.execute("SELECT DISTINCT symbol FROM trades_fifo").fetchall()
    for sym in all_symbols:
        print(f"   - {sym[0]}")

def main():
    """Run the proof of concept"""
    print("\n" + "#" * 80)
    print("#" + " SYMBOL BUG PROOF OF CONCEPT".center(78) + "#")
    print("#" * 80)
    print(f"\nTest started: {datetime.now()}")
    
    # Create test database
    conn = create_test_database()
    
    try:
        # Test current behavior
        realized_df = test_current_behavior(conn)
        
        # Test the matching logic
        test_symbol_matching_logic(conn)
        
        # Conclusion
        print("\n" + "=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        
        if len(realized_df) > 0:
            print("\n⚠️ BUG CONFIRMED: Cross-symbol matching is happening!")
            print("The SQL query correctly filters by symbol, but positions")
            print("are being matched anyway. This suggests the issue is")
            print("elsewhere in the logic.")
        else:
            print("\n✅ No cross-symbol matching occurred.")
            print("The bug may be more complex than initially thought.")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    print(f"\nTest completed: {datetime.now()}")
    print("#" * 80)

if __name__ == "__main__":
    main()