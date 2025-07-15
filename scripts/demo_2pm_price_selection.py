"""
Demo showing 2pm file selection and PX_LAST usage
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_calculator.price_file_selector import PriceFileSelector, EXPORT_WINDOWS
from datetime import datetime, time
import pytz

def demo_price_selection_logic():
    """Demonstrate the price selection logic."""
    
    selector = PriceFileSelector()
    chicago_tz = pytz.timezone('America/Chicago')
    
    print("Price File Selection Logic Demo")
    print("=" * 80)
    
    print("\nValid Export Windows:")
    for window_name, config in EXPORT_WINDOWS.items():
        start = config['start'].strftime('%I:%M %p')
        end = config['end'].strftime('%I:%M %p')
        col = config['price_column']
        print(f"  {window_name}: {start} - {end} → {col}")
    
    print("\n" + "-" * 80)
    print("File Selection Strategy:")
    print("  • Only consider files from 2pm and 4pm windows")
    print("  • Ignore all 3pm files")
    print("  • After 4:30pm, prefer today's 4pm file if available")
    print("  • Otherwise, use most recent valid file")
    
    print("\n" + "-" * 80)
    print("Example Scenarios:")
    
    scenarios = [
        ("9:00 AM", "Most recent valid file (could be yesterday's 4pm)"),
        ("2:15 PM", "Today's 2pm file if available, else most recent"),
        ("3:30 PM", "Most recent valid file (2pm or yesterday's 4pm)"),
        ("4:30 PM", "Today's 4pm file if available, else most recent"),
        ("6:00 PM", "Today's 4pm file preferred, else most recent"),
    ]
    
    for time_str, expected in scenarios:
        print(f"\n{time_str}: {expected}")
    
    print("\n" + "-" * 80)
    print("Current Behavior with Our Test Data:")
    print("  • We have 2pm files: Options_20250712_1400.csv")
    print("  • We have 4pm files: Options_20250714_1600.csv (more recent)")
    print("  • Result: 4pm file is always selected as most recent")
    print("\nTo see 2pm/PX_LAST behavior, we would need:")
    print("  • A 2pm file from today with no 4pm file yet")
    print("  • Or to test at a time before any 4pm files exist")

if __name__ == "__main__":
    demo_price_selection_logic() 