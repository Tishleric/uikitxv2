"""
Test price selection in different time scenarios
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pytz

# Import the integration test function
from test_phase1_integration_fixed import process_trades_with_translation, lookup_market_prices, generate_integration_report

def test_price_selection_at_different_times():
    """Test price selection behavior at different times of day."""
    
    chicago_tz = pytz.timezone('America/Chicago')
    
    # Test scenarios
    scenarios = [
        ("Morning - should use previous day's 4pm", datetime(2025, 7, 14, 9, 0)),
        ("After 2pm export", datetime(2025, 7, 14, 14, 15)),
        ("Between 2pm and 4pm", datetime(2025, 7, 14, 15, 30)),
        ("After 4pm export", datetime(2025, 7, 14, 16, 15)),
        ("Evening - should use 4pm", datetime(2025, 7, 14, 18, 0)),
    ]
    
    print("Testing Price Selection at Different Times")
    print("=" * 80)
    
    # Process trades once
    trade_file = "data/input/trade_ledger/trades_20250714.csv"
    processed_trades = process_trades_with_translation(trade_file)
    
    for desc, test_time in scenarios:
        chicago_time = chicago_tz.localize(test_time)
        
        print(f"\n{desc}")
        print(f"Current time: {chicago_time.strftime('%Y-%m-%d %H:%M %Z')}")
        
        # Look up prices with specific time
        trades_with_prices = lookup_market_prices(
            processed_trades.copy(),
            "data/input/market_prices/options",
            chicago_time
        )
        
        # Show price source distribution
        price_sources = trades_with_prices['price_source'].value_counts()
        print("\nPrice sources used:")
        for source, count in price_sources.items():
            print(f"  {source}: {count}")
        
        # Check if using PX_LAST or PX_SETTLE
        if 'PX_LAST' in price_sources:
            print("  → Using 2pm export (PX_LAST)")
        elif 'PX_SETTLE' in price_sources:
            print("  → Using 4pm export (PX_SETTLE)")


def test_edge_cases():
    """Test edge cases like missing files or boundary times."""
    
    print("\n" + "=" * 80)
    print("Testing Edge Cases")
    print("=" * 80)
    
    from lib.trading.pnl_calculator.price_file_selector import PriceFileSelector
    selector = PriceFileSelector()
    
    # Test boundary times
    boundary_tests = [
        ("Exactly 1:45pm (start of 2pm window)", datetime(2025, 7, 14, 13, 45)),
        ("Exactly 2:30pm (end of 2pm window)", datetime(2025, 7, 14, 14, 30)),
        ("Exactly 3:45pm (start of 4pm window)", datetime(2025, 7, 14, 15, 45)),
        ("Exactly 4:30pm (end of 4pm window)", datetime(2025, 7, 14, 16, 30)),
    ]
    
    chicago_tz = pytz.timezone('America/Chicago')
    
    for desc, test_time in boundary_tests:
        dt = chicago_tz.localize(test_time)
        window = selector.classify_export_time(dt)
        print(f"\n{desc}: {window or 'Not in window'}")


if __name__ == "__main__":
    test_price_selection_at_different_times()
    test_edge_cases() 