"""
Deep diagnostic trace of pnl_engine.py matching logic
Shows exactly what happens at each step of trade processing
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath('../..'))

from datetime import datetime
from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade

def trace_process_new_trade(conn, new_trade, method='fifo'):
    """
    Instrumented version of process_new_trade that shows every detail
    """
    print("\n" + "="*80)
    print(f"TRACING process_new_trade() - Method: {method.upper()}")
    print("="*80)
    
    print("\n### 1. INCOMING TRADE ###")
    print(f"Trade Details:")
    for key, value in new_trade.items():
        print(f"  {key}: {value}")
    
    # Setup
    cursor = conn.cursor()
    table_suffix = method.lower()
    remaining_qty = new_trade['quantity']
    
    print(f"\nInitial remaining quantity to match: {remaining_qty}")
    
    # Determine opposite side
    opposite_side = 'S' if new_trade['buySell'] == 'B' else 'B'
    print(f"Looking for opposite side: {opposite_side} (incoming is {new_trade['buySell']})")
    
    # Build the matching query
    positions_query = f"""
        SELECT sequenceId, transactionId, symbol, price, quantity, time 
        FROM trades_{table_suffix} 
        WHERE symbol = ? AND buySell = ? AND quantity > 0
        ORDER BY sequenceId {'ASC' if method == 'fifo' else 'DESC'}
    """
    
    print("\n### 2. MATCHING QUERY ###")
    print(f"SQL Query:\n{positions_query}")
    print(f"Parameters: ('{new_trade['symbol']}', '{opposite_side}')")
    
    # Execute query
    positions = cursor.execute(positions_query, (new_trade['symbol'], opposite_side)).fetchall()
    
    print(f"\n### 3. POSITIONS FOUND: {len(positions)} ###")
    if positions:
        print("\nPositions that match the criteria:")
        print(f"{'SeqID':<15} {'TransID':<10} {'Symbol':<20} {'Price':<10} {'Qty':<10} {'Time'}")
        print("-" * 85)
        for pos in positions:
            print(f"{pos[0]:<15} {pos[1]:<10} {pos[2]:<20} {pos[3]:<10.4f} {pos[4]:<10.1f} {pos[5]}")
    else:
        print("No matching positions found!")
    
    # Let's also check what positions exist regardless of symbol
    print("\n### 4. ALL AVAILABLE POSITIONS (DEBUG) ###")
    all_positions_query = f"""
        SELECT symbol, buySell, COUNT(*) as count, SUM(quantity) as total_qty
        FROM trades_{table_suffix}
        WHERE quantity > 0
        GROUP BY symbol, buySell
        ORDER BY symbol, buySell
    """
    all_positions = cursor.execute(all_positions_query).fetchall()
    
    print(f"\nAll positions in trades_{table_suffix}:")
    print(f"{'Symbol':<20} {'Side':<6} {'Count':<8} {'Total Qty'}")
    print("-" * 50)
    for pos in all_positions:
        print(f"{pos[0]:<20} {pos[1]:<6} {pos[2]:<8} {pos[3]:>10.1f}")
    
    # Process matches
    realized_trades = []
    print(f"\n### 5. PROCESSING MATCHES ###")
    
    for i, pos in enumerate(positions):
        if remaining_qty <= 0:
            print(f"\nNo more quantity to match, stopping.")
            break
            
        pos_seq_id, pos_trans_id, pos_symbol, pos_price, pos_qty, pos_time = pos
        offset_qty = min(remaining_qty, pos_qty)
        
        print(f"\nMatch #{i+1}:")
        print(f"  Position: {pos_seq_id} ({pos_symbol})")
        print(f"  Position qty: {pos_qty}, Remaining to match: {remaining_qty}")
        print(f"  Will offset: {offset_qty}")
        
        # Calculate P&L
        if opposite_side == 'S':  # We're buying, offsetting a short
            realized_pnl = (pos_price - new_trade['price']) * offset_qty * 1000
            entry_price = pos_price
            exit_price = new_trade['price']
            print(f"  P&L Calc (Short): ({pos_price} - {new_trade['price']}) * {offset_qty} * 1000 = {realized_pnl}")
        else:  # We're selling, offsetting a long
            realized_pnl = (new_trade['price'] - pos_price) * offset_qty * 1000
            entry_price = pos_price
            exit_price = new_trade['price']
            print(f"  P&L Calc (Long): ({new_trade['price']} - {pos_price}) * {offset_qty} * 1000 = {realized_pnl}")
        
        # Create realized trade record
        realized_trade = {
            'symbol': new_trade['symbol'],  # <-- THIS IS THE BUG!
            'sequenceIdBeingOffset': pos_seq_id,
            'sequenceIdDoingOffsetting': new_trade['sequenceId'],
            'partialFull': 'full' if offset_qty == pos_qty else 'partial',
            'quantity': offset_qty,
            'entryPrice': entry_price,
            'exitPrice': exit_price,
            'realizedPnL': realized_pnl,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"\n  Realized Trade Record:")
        print(f"    symbol: {realized_trade['symbol']} (from new_trade)")
        print(f"    *** POSITION SYMBOL WAS: {pos_symbol} ***")
        if realized_trade['symbol'] != pos_symbol:
            print(f"    ⚠️  WARNING: SYMBOL MISMATCH! Recording as {realized_trade['symbol']} instead of {pos_symbol}")
        
        realized_trades.append(realized_trade)
        
        # Update database
        if offset_qty == pos_qty:
            print(f"  Action: DELETE position {pos_seq_id} (fully offset)")
        else:
            print(f"  Action: UPDATE position {pos_seq_id} quantity to {pos_qty - offset_qty}")
        
        remaining_qty -= offset_qty
    
    print(f"\n### 6. FINAL RESULTS ###")
    print(f"Realized trades created: {len(realized_trades)}")
    print(f"Remaining quantity after matching: {remaining_qty}")
    
    if remaining_qty > 0:
        print(f"\nWill INSERT new position for remaining {remaining_qty} qty")
    
    return realized_trades


def test_specific_scenario(db_path='../../trades.db'):
    """Test a specific problematic scenario"""
    conn = sqlite3.connect(db_path)
    
    print("\n" + "#"*80)
    print("# TESTING CROSS-SYMBOL MATCHING SCENARIO")
    print("#"*80)
    
    # First, let's see what's in the database for our problem trades
    print("\n### CURRENT DATABASE STATE ###")
    
    # Check trades_fifo for relevant positions
    query = """
    SELECT sequenceId, symbol, buySell, quantity, price
    FROM trades_fifo
    WHERE symbol IN ('USU5 Comdty', 'TYU5 Comdty', 'TYWQ25C1 112.25 Comdty')
    AND quantity > 0
    ORDER BY symbol, sequenceId
    """
    
    positions = conn.execute(query).fetchall()
    
    print("\nCurrent positions in trades_fifo:")
    print(f"{'SeqID':<15} {'Symbol':<25} {'Side':<5} {'Qty':<10} {'Price'}")
    print("-" * 70)
    for pos in positions:
        print(f"{pos[0]:<15} {pos[1]:<25} {pos[2]:<5} {pos[3]:<10.1f} {pos[4]:<10.4f}")
    
    # Check realized trades
    print("\n### RECENT REALIZED TRADES ###")
    query = """
    SELECT symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting, quantity, realizedPnL
    FROM realized_fifo
    WHERE sequenceIdDoingOffsetting = '20250804-478'
    OR sequenceIdBeingOffset IN ('20250801-473', '20250801-474')
    ORDER BY timestamp DESC
    LIMIT 20
    """
    
    realized = conn.execute(query).fetchall()
    
    print("\nRealized trades involving our problem trades:")
    print(f"{'Symbol':<25} {'Being Offset':<15} {'Doing Offset':<15} {'Qty':<8} {'P&L'}")
    print("-" * 85)
    for r in realized:
        print(f"{r[0]:<25} {r[1]:<15} {r[2]:<15} {r[3]:<8.1f} {r[4]:>10.2f}")
    
    # Now let's trace what would happen with a new trade
    print("\n### SIMULATING A NEW TRADE ###")
    
    # Simulate the problematic TYU5 trade
    test_trade = {
        'transactionId': 999,
        'symbol': 'TYU5 Comdty',
        'price': 108.5,
        'quantity': 3.0,
        'buySell': 'S',  # Sell
        'sequenceId': 'TEST-999',
        'time': '2025-08-04 12:00:00.000',
        'fullPartial': 'full'
    }
    
    # Trace the matching process
    trace_process_new_trade(conn, test_trade, 'fifo')
    
    conn.close()


def check_symbol_integrity(db_path='../../trades.db'):
    """Check for any symbol encoding or integrity issues"""
    conn = sqlite3.connect(db_path)
    
    print("\n" + "#"*80)
    print("# SYMBOL INTEGRITY CHECK")
    print("#"*80)
    
    # Check for any weird symbol values
    print("\n### CHECKING FOR SYMBOL ANOMALIES ###")
    
    query = """
    SELECT DISTINCT symbol, LENGTH(symbol) as len, HEX(symbol) as hex_val
    FROM trades_fifo
    WHERE quantity > 0
    ORDER BY symbol
    """
    
    symbols = conn.execute(query).fetchall()
    
    print(f"\n{'Symbol':<30} {'Length':<10} {'First 20 hex chars'}")
    print("-" * 65)
    for symbol, length, hex_val in symbols:
        print(f"{symbol:<30} {length:<10} {hex_val[:40]}")
    
    # Check for symbols that look similar but aren't equal
    print("\n### CHECKING FOR SIMILAR BUT DIFFERENT SYMBOLS ###")
    
    query = """
    SELECT DISTINCT a.symbol as symbol1, b.symbol as symbol2
    FROM trades_fifo a, trades_fifo b
    WHERE a.symbol != b.symbol
    AND a.symbol LIKE '%' || SUBSTR(b.symbol, 1, 4) || '%'
    AND a.quantity > 0
    AND b.quantity > 0
    """
    
    similar = conn.execute(query).fetchall()
    
    if similar:
        print("\nFound similar symbols that are treated as different:")
        for s1, s2 in similar:
            print(f"  '{s1}' vs '{s2}'")
    else:
        print("\nNo similar symbols found.")
    
    conn.close()


if __name__ == "__main__":
    print("PNL ENGINE DEEP DIAGNOSTIC TRACE")
    print("================================")
    print(f"Started: {datetime.now()}")
    
    # Run the specific scenario test
    test_specific_scenario()
    
    # Check symbol integrity
    check_symbol_integrity()
    
    print(f"\nCompleted: {datetime.now()}")