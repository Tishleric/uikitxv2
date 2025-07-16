"""Test price mapping end-to-end for all positions."""

import sys
sys.path.append('.')
from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager
from datetime import datetime

print("=== TESTING PRICE MAPPING END-TO-END ===\n")

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
pm = PositionManager(storage)

# Get all positions
positions = pm.get_positions()
print(f"Found {len(positions)} positions\n")

# Test price lookup for each position
success_count = 0
for pos in positions:
    instrument = pos['instrument_name']
    print(f"{instrument}:")
    print(f"  Position: {pos['position_quantity']}")
    
    # Test price lookup
    price, source = storage.get_market_price(instrument, datetime.now())
    
    if price is not None:
        success_count += 1
        print(f"  ✓ Price: {price} (source: {source})")
        print(f"  Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    else:
        print(f"  ❌ No price found")
        
        # Debug: Show what Bloomberg symbol we're looking for
        mapped = storage._map_to_bloomberg(instrument)
        print(f"  Maps to: {mapped}")
        
        # Check if this symbol exists in database
        import sqlite3
        conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
        cursor = conn.cursor()
        
        if mapped:
            cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg = ?", (mapped,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  Symbol exists in DB!")
                cursor.execute("SELECT px_settle, px_last FROM market_prices WHERE bloomberg = ? LIMIT 1", (mapped,))
                row = cursor.fetchone()
                print(f"  DB values: settle={row[0]}, last={row[1]}")
            else:
                print(f"  Symbol NOT in database")
                # Try partial match
                base = mapped.split()[0]
                cursor.execute("SELECT COUNT(*) FROM market_prices WHERE bloomberg LIKE ?", (f"{base}%",))
                partial_count = cursor.fetchone()[0]
                print(f"  Partial matches for {base}: {partial_count}")
        
        conn.close()
    print()

print(f"\nSUMMARY: {success_count}/{len(positions)} positions have prices")

# Update market prices in position manager
print("\nUpdating market prices in position manager...")
pm.update_market_prices()

# Check positions again
print("\nPositions after update:")
positions_after = pm.get_positions()
with_prices = sum(1 for p in positions_after if p.get('last_market_price') is not None)
print(f"Positions with market prices: {with_prices}/{len(positions_after)}")

# Show P&L summary
total_unrealized = sum(p.get('unrealized_pnl', 0) for p in positions_after)
total_realized = sum(p.get('total_realized_pnl', 0) for p in positions_after)
print(f"\nTotal Unrealized P&L: ${total_unrealized:.2f}")
print(f"Total Realized P&L: ${total_realized:.2f}")
print(f"Total P&L: ${(total_unrealized + total_realized):.2f}") 