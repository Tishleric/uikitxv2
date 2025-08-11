"""
Verify that the Live PnL fix works correctly.
This script tests that price updates trigger PnL recalculation.
"""

import sqlite3
import time
import redis
from datetime import datetime
import pytz

from lib.trading.pnl_fifo_lifo import update_current_price, load_pricing_dictionaries
from lib.trading.pnl_fifo_lifo.pnl_engine import calculate_unrealized_pnl
from lib.trading.pnl_fifo_lifo.data_manager import view_unrealized_positions


def main():
    """Test the Live PnL fix"""
    
    print("=== Live PnL Fix Verification ===")
    
    # Connect to database
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    # Test symbol
    test_symbol = "TYU5 Comdty"
    
    # 1. Check initial state
    print("\n1. Initial State:")
    result = cursor.execute("""
        SELECT fifo_unrealized_pnl, last_updated 
        FROM positions 
        WHERE symbol = ?
    """, (test_symbol,)).fetchone()
    
    if result:
        initial_unrealized = result[0]
        print(f"  Initial unrealized PnL: {initial_unrealized}")
        print(f"  Last updated: {result[1]}")
    else:
        print("  No position found for", test_symbol)
        conn.close()
        return
    
    # 2. Get current price and update it
    print("\n2. Updating Price:")
    chicago_tz = pytz.timezone('America/Chicago')
    now = datetime.now(chicago_tz)
    
    # Get current 'now' price and change it slightly
    current_price_row = cursor.execute("""
        SELECT price FROM pricing 
        WHERE symbol = ? AND price_type = 'now'
    """, (test_symbol,)).fetchone()
    
    if current_price_row:
        current_price = current_price_row[0]
        new_price = current_price + 0.125  # Move price by 1/8
    else:
        new_price = 112.500  # Default price
        
    print(f"  Updating price to: {new_price}")
    
    # Update price (this should now trigger Redis signal)
    success = update_current_price(conn, test_symbol, new_price, now)
    print(f"  Update success: {success}")
    
    # 3. Wait a bit for aggregator to process
    print("\n3. Waiting for aggregator to process...")
    time.sleep(2)
    
    # 4. Check if unrealized PnL changed
    print("\n4. Checking Updated State:")
    result = cursor.execute("""
        SELECT fifo_unrealized_pnl, last_updated 
        FROM positions 
        WHERE symbol = ?
    """, (test_symbol,)).fetchone()
    
    if result:
        new_unrealized = result[0]
        print(f"  New unrealized PnL: {new_unrealized}")
        print(f"  Last updated: {result[1]}")
        
        if new_unrealized != initial_unrealized:
            print(f"  ✅ SUCCESS: Unrealized PnL changed from {initial_unrealized} to {new_unrealized}")
        else:
            print(f"  ❌ FAILED: Unrealized PnL did not change")
            
            # Do manual calculation to verify
            print("\n5. Manual Calculation Check:")
            positions_df = view_unrealized_positions(conn, 'fifo', symbol=test_symbol)
            price_dicts = load_pricing_dictionaries(conn)
            
            unrealized_list = calculate_unrealized_pnl(positions_df, price_dicts, 'live')
            manual_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
            
            print(f"  Manual calculation: {manual_unrealized}")
            print(f"  Position count: {len(positions_df)}")
            
            # Check if aggregator is running
            print("\n6. Checking Redis Connection:")
            try:
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                print("  Redis is running")
                
                # Try publishing a test message
                subscribers = r.publish("positions:changed", "test")
                print(f"  Redis subscribers on positions:changed: {subscribers}")
                
                if subscribers == 0:
                    print("  ⚠️  No aggregator subscribed to positions:changed!")
                    print("  Make sure positions_aggregator is running")
            except Exception as e:
                print(f"  Redis error: {e}")
    
    conn.close()
    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    main()