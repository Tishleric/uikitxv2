"""
Test live trade processing to determine if the issue is data corruption or active bug
"""
import sqlite3
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Add the pnl module to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def create_test_trades(conn):
    """Insert controlled test trades to monitor processing"""
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CREATING TEST TRADES")
    print("=" * 80)
    
    # Get current timestamp
    now = datetime.now()
    trade_time = now.strftime('%Y-%m-%d %H:%M:%S.000')
    
    # Create unique sequence IDs based on current time
    base_id = now.strftime('%Y%m%d')
    start_seq = 9000  # High number to avoid conflicts
    
    # Test trades - carefully designed to test offsetting
    test_trades = [
        # Buy 5 TYU5
        {
            'transactionId': f'TEST-{start_seq}',
            'symbol': 'TYU5 Comdty',
            'price': 112.50,
            'quantity': 5.0,
            'buySell': 'B',
            'sequenceId': f'{base_id}-{start_seq}',
            'time': trade_time,
            'fullPartial': 'full'
        },
        # Buy 3 USU5 
        {
            'transactionId': f'TEST-{start_seq+1}',
            'symbol': 'USU5 Comdty',
            'price': 115.75,
            'quantity': 3.0,
            'buySell': 'B',
            'sequenceId': f'{base_id}-{start_seq+1}',
            'time': trade_time,
            'fullPartial': 'full'
        }
    ]
    
    # Insert test trades into both FIFO and LIFO tables
    for method in ['fifo', 'lifo']:
        for trade in test_trades:
            insert_query = f"""
            INSERT INTO trades_{method} 
            (transactionId, symbol, price, original_price, quantity, buySell, 
             sequenceId, time, original_time, fullPartial)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                trade['transactionId'],
                trade['symbol'],
                trade['price'],
                trade['price'],  # original_price
                trade['quantity'],
                trade['buySell'],
                trade['sequenceId'],
                trade['time'],
                trade['time'],  # original_time
                trade['fullPartial']
            ))
    
    conn.commit()
    
    print("Created test trades:")
    for trade in test_trades:
        print(f"  {trade['sequenceId']}: {trade['buySell']} {trade['quantity']} {trade['symbol']} @ {trade['price']}")
    
    return test_trades, base_id, start_seq

def monitor_trades_status(conn, test_trades):
    """Check the current status of our test trades"""
    print("\n" + "=" * 80)
    print("MONITORING TEST TRADES STATUS")
    print("=" * 80)
    
    # Check trades_fifo
    for method in ['fifo', 'lifo']:
        print(f"\n### Status in trades_{method} ###")
        
        trade_ids = "','".join([t['sequenceId'] for t in test_trades])
        query = f"""
        SELECT sequenceId, symbol, quantity, buySell, price
        FROM trades_{method}
        WHERE sequenceId IN ('{trade_ids}')
        """
        
        result = pd.read_sql_query(query, conn)
        if len(result) > 0:
            print(result.to_string(index=False))
        else:
            print("No test trades found (may have been offset)")
    
    # Check realized trades
    print("\n### Realized Trades ###")
    
    trade_ids = "','".join([t['sequenceId'] for t in test_trades])
    realized_query = f"""
    SELECT 
        symbol,
        sequenceIdBeingOffset,
        sequenceIdDoingOffsetting,
        quantity,
        realizedPnL,
        timestamp
    FROM realized_fifo
    WHERE sequenceIdBeingOffset IN ('{trade_ids}')
       OR sequenceIdDoingOffsetting IN ('{trade_ids}')
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    realized = pd.read_sql_query(realized_query, conn)
    if len(realized) > 0:
        print("\nTest trades involved in realizations:")
        print(realized.to_string(index=False))

def create_offsetting_trade(conn, symbol, quantity, price, base_id, seq_num):
    """Create an offsetting (sell) trade to trigger realization"""
    print(f"\n### Creating offsetting trade: SELL {quantity} {symbol} ###")
    
    cursor = conn.cursor()
    now = datetime.now()
    trade_time = now.strftime('%Y-%m-%d %H:%M:%S.000')
    
    offset_trade = {
        'transactionId': f'TEST-OFFSET-{seq_num}',
        'symbol': symbol,
        'price': price,
        'quantity': quantity,
        'buySell': 'S',
        'sequenceId': f'{base_id}-{seq_num}',
        'time': trade_time
    }
    
    # Process this trade through the PnL engine
    from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
    
    # Process for both methods
    for method in ['fifo', 'lifo']:
        print(f"\nProcessing offset trade through {method.upper()}...")
        realized = process_new_trade(conn, offset_trade, method, trade_time)
        
        if realized:
            print(f"Realized {len(realized)} trades:")
            for r in realized:
                print(f"  Offset {r['sequenceIdBeingOffset']} with {r['sequenceIdDoingOffsetting']}")
                print(f"  Symbol: {r['symbol']}, Qty: {r['quantity']}, PnL: {r['realizedPnL']}")
        else:
            print("No trades were realized")
    
    conn.commit()
    return offset_trade

def check_cross_symbol_matching(conn):
    """Check if any cross-symbol matching occurred"""
    print("\n" + "=" * 80)
    print("CHECKING FOR CROSS-SYMBOL MATCHING")
    print("=" * 80)
    
    # Look for any realized trades where the symbols don't match
    cross_check_query = """
    SELECT 
        r.symbol as realized_symbol,
        r.sequenceIdBeingOffset,
        r.sequenceIdDoingOffsetting,
        t1.symbol as offset_symbol,
        t2.symbol as offsetting_symbol
    FROM realized_fifo r
    LEFT JOIN trades_fifo t1 ON r.sequenceIdBeingOffset = t1.sequenceId
    LEFT JOIN trades_fifo t2 ON r.sequenceIdDoingOffsetting = t2.sequenceId
    WHERE DATE(r.timestamp) = DATE('now')
    """
    
    cross_matches = pd.read_sql_query(cross_check_query, conn)
    
    if len(cross_matches) > 0:
        # Check for mismatches
        mismatches = cross_matches[
            (cross_matches['realized_symbol'] != cross_matches['offset_symbol']) |
            (cross_matches['realized_symbol'] != cross_matches['offsetting_symbol'])
        ]
        
        if len(mismatches) > 0:
            print("\n⚠️ FOUND CROSS-SYMBOL MATCHING!")
            print(mismatches.to_string(index=False))
            return True
        else:
            print("\n✅ No cross-symbol matching found - all symbols match correctly")
            return False
    else:
        print("\nNo realized trades found today")
        return False

def main():
    """Run the live processing test"""
    print("\n" + "#" * 80)
    print("#" + " LIVE TRADE PROCESSING TEST".center(78) + "#")
    print("#" * 80)
    print(f"\nTest started: {datetime.now()}")
    
    # Connect to database
    conn = sqlite3.connect('../../trades.db')
    
    try:
        # Step 1: Create test trades
        test_trades, base_id, start_seq = create_test_trades(conn)
        
        # Step 2: Monitor initial status
        monitor_trades_status(conn, test_trades)
        
        # Step 3: Create offsetting trades
        print("\n" + "=" * 80)
        print("CREATING OFFSETTING TRADES")
        print("=" * 80)
        
        # Offset TYU5 trade
        offset1 = create_offsetting_trade(conn, 'TYU5 Comdty', 3.0, 112.75, base_id, start_seq + 10)
        time.sleep(1)  # Small delay
        
        # Offset USU5 trade  
        offset2 = create_offsetting_trade(conn, 'USU5 Comdty', 2.0, 115.50, base_id, start_seq + 11)
        
        # Step 4: Check final status
        print("\n" + "=" * 80)
        print("FINAL STATUS CHECK")
        print("=" * 80)
        
        monitor_trades_status(conn, test_trades + [offset1, offset2])
        
        # Step 5: Check for cross-symbol matching
        has_cross_match = check_cross_symbol_matching(conn)
        
        # Step 6: Check if realized trades were properly removed
        print("\n" + "=" * 80)
        print("CHECKING TRADE CLEANUP")
        print("=" * 80)
        
        cleanup_check = """
        SELECT 
            r.sequenceIdBeingOffset,
            r.quantity as realized_qty,
            t.quantity as remaining_qty
        FROM realized_fifo r
        LEFT JOIN trades_fifo t ON r.sequenceIdBeingOffset = t.sequenceId
        WHERE DATE(r.timestamp) = DATE('now')
          AND r.sequenceIdBeingOffset LIKE 'TEST-%'
        """
        
        cleanup = pd.read_sql_query(cleanup_check, conn)
        if len(cleanup) > 0:
            print("\nRealized trades and their remaining quantities:")
            print(cleanup.to_string(index=False))
            
            # Check for trades that should have been removed
            should_be_gone = cleanup[cleanup['remaining_qty'].notna()]
            if len(should_be_gone) > 0:
                print("\n⚠️ WARNING: Some realized trades still exist in trades_fifo!")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if has_cross_match:
            print("❌ ACTIVE BUG: Cross-symbol matching is occurring with new trades!")
            print("   This is NOT just data corruption - the bug is still active.")
        else:
            print("✅ No cross-symbol matching with new trades")
            print("   The cross-symbol issue may be historical data corruption.")
        
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