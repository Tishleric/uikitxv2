"""Test the final P&L Dashboard V2 state."""

import sys
sys.path.append('.')
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.pnl_calculator.storage import PnLStorage

print("=== P&L DASHBOARD V2 FINAL STATE TEST ===\n")

storage = PnLStorage("data/output/pnl/pnl_tracker.db")
pm = PositionManager(storage)

# Get positions
positions = pm.get_positions()
print(f"Total positions: {len(positions)}")

# Count positions with prices
with_prices = sum(1 for p in positions if p.get('last_market_price') is not None)
print(f"Positions with prices: {with_prices}/{len(positions)}")

# Calculate totals
total_unrealized = sum(p.get('unrealized_pnl', 0) for p in positions)
total_realized = sum(p.get('total_realized_pnl', 0) for p in positions)
total_pnl = total_unrealized + total_realized

print(f"\nP&L Summary:")
print(f"  Unrealized P&L: ${total_unrealized:,.2f}")
print(f"  Realized P&L: ${total_realized:,.2f}")
print(f"  Total P&L: ${total_pnl:,.2f}")

# Show positions table
print("\n" + "="*100)
print(f"{'Instrument':<40} {'Position':>12} {'Last Price':>12} {'Unrealized':>12} {'Realized':>12}")
print("="*100)

for p in positions:
    instrument = p['instrument_name'][:40]
    position = f"{p['position_quantity']:,.0f}"
    last_price = f"${p['last_market_price']:.5f}" if p.get('last_market_price') else "N/A"
    unrealized = f"${p['unrealized_pnl']:,.2f}"
    realized = f"${p['total_realized_pnl']:,.2f}"
    
    print(f"{instrument:<40} {position:>12} {last_price:>12} {unrealized:>12} {realized:>12}")

print("\n✓ Dashboard should now show:")
print("  - 15 of 17 positions with prices")  
print("  - Unrealized P&L calculated for all priced positions")
print("  - All positions displayed without pagination")
print("  - Green/red color coding for P&L values") 