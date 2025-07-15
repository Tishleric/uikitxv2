"""
Test the Symbol Translator with futures support
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.symbol_translator import SymbolTranslator
from datetime import datetime

def test_futures_translation():
    translator = SymbolTranslator()
    
    # Test cases for futures
    futures_test_cases = [
        # Actant format -> Expected Bloomberg format
        ("XCMEFFDPSX20250919U0ZN", "TYU5 Comdty"),  # 10-Year Sept 2025
        ("XCMEFFDPSX20250918U0TY", "TYU5 Comdty"),  # TY already correct
        ("XCMEFFDPSX20250919U0TU", "TUU5 Comdty"),  # 2-Year Sept 2025
        ("XCMEFFDPSX20250919U0FV", "FVU5 Comdty"),  # 5-Year Sept 2025
        ("XCMEFFDPSX20250919U0US", "USU5 Comdty"),  # Ultra Bond Sept 2025
        ("XCMEFFDPSX20250919U0RX", "RXU5 Comdty"),  # Euro-Bund Sept 2025
        
        # Different months
        ("XCMEFFDPSX20250619M0ZN", "TYM5 Comdty"),  # June 2025
        ("XCMEFFDPSX20251219Z0ZN", "TYZ5 Comdty"),  # December 2025
        ("XCMEFFDPSX20260319H0ZN", "TYH6 Comdty"),  # March 2026
    ]
    
    print("Testing Futures Translation:")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for actant_symbol, expected in futures_test_cases:
        result = translator.translate(actant_symbol)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            passed += 1
        else:
            failed += 1
            
        print(f"{status}: {actant_symbol}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
    
    print(f"Futures Summary: {passed} passed, {failed} failed")
    
    # Test some options to ensure they still work
    print("\n" + "=" * 80)
    print("Testing Options (regression check):")
    
    options_test_cases = [
        ("XCMEOCADPS20250714N0VY2/108.75", "VBYN25C2 108.750 Comdty"),
        ("XCMEOPADPS20250714N0VY2/109.5", "VBYN25P2 109.500 Comdty"),
        ("XCMEOCADPS20250718N0ZN3/111.5", "3MN5C 111.500 Comdty"),
    ]
    
    options_passed = 0
    options_failed = 0
    
    for actant_symbol, expected in options_test_cases:
        result = translator.translate(actant_symbol)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            options_passed += 1
        else:
            options_failed += 1
            
        print(f"{status}: {actant_symbol}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
    
    print(f"Options Summary: {options_passed} passed, {options_failed} failed")
    
    # Test with real trade data
    print("\n" + "=" * 80)
    print("Testing with actual trade symbols:")
    
    actual_symbols = [
        "XCMEFFDPSX20250919U0ZN",  # From trades_20250714.csv
        "XCMEFFDPSX20250918U0TY",  # From mock trades
    ]
    
    for symbol in actual_symbols:
        result = translator.translate(symbol)
        print(f"{symbol} -> {result}")

if __name__ == "__main__":
    test_futures_translation() 