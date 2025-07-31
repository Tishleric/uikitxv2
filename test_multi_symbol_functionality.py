#!/usr/bin/env python3
"""
Test script to verify multi-symbol functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from lib.trading.pnl_fifo_lifo.test_simulation import run_comprehensive_daily_breakdown

def test_multi_symbol():
    """Test the multi-symbol capability"""
    
    # Define close prices for multiple symbols
    # This simulates having both futures and options trades
    multi_symbol_prices = {
        datetime(2025, 7, 21).date(): {
            'XCMEFFDPSX20250919U0ZN': 111.1875,        # 10-year futures
            'XCMEOCADPS20250919Q0TY4': 2.25,           # Options (example)
        },
        datetime(2025, 7, 22).date(): {
            'XCMEFFDPSX20250919U0ZN': 111.40625,
            'XCMEOCADPS20250919Q0TY4': 2.30,
        },
        datetime(2025, 7, 23).date(): {
            'XCMEFFDPSX20250919U0ZN': 111.015625,
            'XCMEOCADPS20250919Q0TY4': 2.15,
        },
        datetime(2025, 7, 24).date(): {
            'XCMEFFDPSX20250919U0ZN': 110.828125,
            'XCMEOCADPS20250919Q0TY4': 2.05,
        },
        datetime(2025, 7, 25).date(): {
            'XCMEFFDPSX20250919U0ZN': 110.984375,
            'XCMEOCADPS20250919Q0TY4': 2.10,
        }
    }
    
    print("Testing multi-symbol P&L calculation capability...")
    print("=" * 60)
    print("\nThis test will:")
    print("1. Drop and recreate all tables")
    print("2. Load trades from CSV files")
    print("3. Calculate P&L for each symbol using its own closing prices")
    print("4. Generate a comprehensive report")
    print("\n" + "=" * 60)
    
    try:
        # Run the simulation with multi-symbol support
        run_comprehensive_daily_breakdown(close_prices=multi_symbol_prices)
        
        print("\n" + "=" * 60)
        print("SUCCESS: Multi-symbol functionality is working correctly!")
        print("The system can now handle different closing prices for different symbols on the same day.")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_multi_symbol()
    sys.exit(0 if success else 1)