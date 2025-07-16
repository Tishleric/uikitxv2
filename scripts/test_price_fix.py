"""Test if the price mapping fix works."""

import sys
sys.path.append('.')
from datetime import datetime

print("=== TESTING PRICE MAPPING FIX ===")
print(f"Time: {datetime.now()}\n")

# Test the updated position manager
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.pnl_calculator.storage import PnLStorage

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
position_manager = PositionManager(storage)

print("1. BEFORE UPDATE:")
positions = position_manager.get_positions()
print(f"   Total positions: {len(positions)}")

# Show positions with and without prices
with_prices = 0
without_prices = 0

for pos in positions[:5]:  # Show first 5
    has_price = pos.get('last_market_price') is not None
    if has_price:
        with_prices += 1
    else:
        without_prices += 1
    
    print(f"\n   {pos['instrument_name']}")
    print(f"   • Position: {pos['position_quantity']}")
    print(f"   • Last Price: {pos.get('last_market_price', 'None')}")
    print(f"   • Unrealized P&L: {pos.get('unrealized_pnl', 0)}")

print(f"\n   Summary: {with_prices} with prices, {without_prices} without prices")

# Update market prices
print("\n2. UPDATING MARKET PRICES...")
position_manager.update_market_prices()

# Check again
print("\n3. AFTER UPDATE:")
positions = position_manager.get_positions()

with_prices_after = 0
without_prices_after = 0

for pos in positions[:5]:  # Show first 5 again
    has_price = pos.get('last_market_price') is not None
    if has_price:
        with_prices_after += 1
    else:
        without_prices_after += 1
    
    print(f"\n   {pos['instrument_name']}")
    print(f"   • Position: {pos['position_quantity']}")
    print(f"   • Last Price: {pos.get('last_market_price', 'None')}")
    print(f"   • Unrealized P&L: {pos.get('unrealized_pnl', 0)}")

print(f"\n   Summary: {with_prices_after} with prices, {without_prices_after} without prices")

if with_prices_after > with_prices:
    print("\n✅ SUCCESS: More positions have prices now!")
else:
    print("\n❌ ISSUE: Price mapping still not working")
    
# Test specific instruments
print("\n4. TESTING SPECIFIC INSTRUMENTS:")
test_cases = [
    "XCMEFFDPSX20250919U0ZN",  # Should map to TU
    "XCMEOCADPS20250714N0VY2/110",  # Should find option
]

for inst in test_cases:
    print(f"\n   Testing {inst}:")
    price, source = storage.get_market_price(inst, datetime.now())
    if price:
        print(f"   ✓ Found price: {price} from {source}")
    else:
        print(f"   ❌ No price found")

print("\n✅ TEST COMPLETE") 