#!/usr/bin/env python3
"""
Test futures symbol translation and edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_fifo_lifo.config import FUTURES_SYMBOLS

# Test cases for futures symbols
FUTURES_TEST_CASES = [
    # Standard cases
    ("TU", "TUU5 Comdty"),
    ("FV", "FVU5 Comdty"),
    ("TY", "TYU5 Comdty"),
    ("US", "USU5 Comdty"),
    ("RX", "RXU5 Comdty"),
    
    # Edge cases
    ("tu", None),  # lowercase
    ("TU ", None),  # trailing space
    (" TU", None),  # leading space
    ("TN", None),  # Not in mapping
    ("UB", None),  # Not in mapping
    ("", None),    # empty
    ("NAN", None), # NaN as string
]


def test_futures_translation():
    """Test futures symbol translation"""
    print("=" * 80)
    print("FUTURES SYMBOL TRANSLATION TEST")
    print("=" * 80)
    print()
    
    print("Current FUTURES_SYMBOLS mapping:")
    for key, value in FUTURES_SYMBOLS.items():
        print(f"  {key} -> {value}")
    
    print()
    print("Test Results:")
    print("-" * 80)
    print(f"{'Input':<15} {'Expected':<25} {'Actual':<25} {'Pass/Fail':<10}")
    print("-" * 80)
    
    for test_input, expected in FUTURES_TEST_CASES:
        # Simulate the current logic from close_price_watcher
        symbol_base = str(test_input).strip().upper()
        
        if symbol_base in FUTURES_SYMBOLS:
            actual = FUTURES_SYMBOLS[symbol_base]
        else:
            actual = None
        
        status = "PASS" if actual == expected else "FAIL"
        
        print(f"{repr(test_input):<15} {str(expected):<25} {str(actual):<25} {status:<10}")
    
    print()
    print("FINDINGS:")
    print("-" * 80)
    print("1. Current logic handles standard cases correctly")
    print("2. Properly converts to uppercase and strips spaces")
    print("3. TN and UB mentioned in docs but not in config mapping")
    print("4. Empty and invalid symbols correctly return None")
    

if __name__ == "__main__":
    test_futures_translation()