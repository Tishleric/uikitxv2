#!/usr/bin/env python3
"""
Test script for closed position tracking functionality.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import date
from lib.trading.pnl_calculator.controller import PnLController
from lib.trading.pnl_calculator.closed_position_tracker import ClosedPositionTracker

def main():
    """Test closed position tracking."""
    print("Testing Closed Position Tracking")
    print("=" * 60)
    
    # Initialize controller
    controller = PnLController()
    
    # Update closed positions for today
    today = date.today()
    print(f"\nUpdating closed positions for {today}...")
    controller.update_closed_positions(today)
    
    # Get all positions with closed quantities
    print("\nPositions with Closed Quantities:")
    print("-" * 60)
    positions = controller.get_positions_with_closed()
    
    if not positions:
        print("No positions found in database.")
    else:
        print(f"{'Symbol':<20} {'Open Pos':>10} {'Closed Pos':>12} {'Avg Cost':>10} {'Last Price':>10}")
        print("-" * 60)
        
        for pos in positions:
            symbol = pos['symbol']
            open_pos = pos['open_position']
            closed_pos = pos['closed_position']
            avg_cost = pos['avg_cost'] or 0
            last_price = pos['last_price'] or 0
            
            # Only show rows with activity
            if open_pos != 0 or closed_pos != 0:
                print(f"{symbol:<20} {open_pos:>10.0f} {closed_pos:>12.0f} {avg_cost:>10.4f} {last_price:>10.4f}")
    
    # Test position history for a specific symbol
    print("\n" + "=" * 60)
    test_symbol = "TYU5 Comdty"  # Example symbol
    print(f"\nPosition History for {test_symbol}:")
    print("-" * 60)
    
    tracker = ClosedPositionTracker("data/output/pnl/pnl_tracker.db")
    history = tracker.get_position_history(test_symbol)
    
    if history:
        print(f"{'Date':<12} {'Time':<10} {'Action':<6} {'Qty':>8} {'Price':>10} {'Pos After':>10}")
        print("-" * 60)
        for entry in history[:10]:  # Show first 10 entries
            print(f"{entry['date']:<12} {entry['time']:<10} {entry['action']:<6} "
                  f"{entry['quantity']:>8.0f} {entry['price']:>10.4f} {entry['position_after']:>10.0f}")
        
        if len(history) > 10:
            print(f"... {len(history) - 10} more entries ...")
    else:
        print(f"No trade history found for {test_symbol}")

if __name__ == "__main__":
    main() 