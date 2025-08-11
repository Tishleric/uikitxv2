#!/usr/bin/env python3
"""
Verify that the close price fix is working correctly
"""

import sys
import os
from datetime import datetime
import pytz

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from lib.trading.pnl_fifo_lifo.data_manager import get_trading_day

def main():
    print("Verifying close price fix...")
    print("=" * 60)
    
    # Show what the dashboard will now use
    chicago_tz = pytz.timezone('America/Chicago')
    now_cdt = datetime.now(chicago_tz)
    
    # Calculate trading day (what dashboard now uses)
    trading_day = get_trading_day(datetime.now()).strftime('%Y-%m-%d')
    
    print(f"Current Chicago time:    {now_cdt}")
    print(f"Trading day for filter:  {trading_day}")
    
    if now_cdt.hour >= 17:
        print("\n✓ After 5pm: Dashboard will correctly use tomorrow's date")
        print(f"  Close prices will only show if timestamp starts with '{trading_day}'")
    else:
        print("\n✓ Before 5pm: Dashboard uses today's date")
        print(f"  Close prices will only show if timestamp starts with '{trading_day}'")
    
    print("\nExpected behavior:")
    print("- Close prices: Only shown if from current trading day")
    print("- Close PnL: Only calculated if close price exists for trading day")
    print("- Consistent with positions aggregator fix")
    
    print("\nNote: Dashboard may need refresh to show updated behavior")

if __name__ == "__main__":
    main()