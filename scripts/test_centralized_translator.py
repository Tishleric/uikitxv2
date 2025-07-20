#!/usr/bin/env python3
"""
Test script for centralized symbol translator.

Run this to verify translations work correctly with real data.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.strike_converter import StrikeConverter
from lib.trading.market_prices.centralized_symbol_translator import CentralizedSymbolTranslator


def test_strike_converter():
    """Test strike conversions."""
    print("\n=== Testing Strike Converter ===")
    
    test_cases = [
        ("111", "XCME to decimal"),
        ("111:25", "XCME to decimal"),
        ("111:5", "XCME to decimal (special)"),
        ("111:75", "XCME to decimal"),
    ]
    
    for xcme_strike, desc in test_cases:
        decimal = StrikeConverter.xcme_to_decimal(xcme_strike)
        back_to_xcme = StrikeConverter.decimal_to_xcme(decimal)
        bloomberg_fmt = StrikeConverter.format_strike(xcme_strike, "bloomberg")
        cme_fmt = StrikeConverter.format_strike(xcme_strike, "cme")
        
        print(f"\n{desc}:")
        print(f"  XCME: {xcme_strike} → Decimal: {decimal} → XCME: {back_to_xcme}")
        print(f"  Bloomberg format: {bloomberg_fmt}")
        print(f"  CME format: {cme_fmt}")


def test_symbol_translations():
    """Test full symbol translations."""
    print("\n=== Testing Symbol Translations ===")
    
    translator = CentralizedSymbolTranslator()
    
    # Test cases: (symbol, from_format, to_format, description)
    test_cases = [
        # XCME to Bloomberg
        ("XCME.VY3.21JUL25.111:75.C", "xcme", "bloomberg", "Monday Call"),
        ("XCME.VY3.21JUL25.111:75.P", "xcme", "bloomberg", "Monday Put"),
        ("XCME.GY4.22JUL25.111:5.C", "xcme", "bloomberg", "Tuesday Call"),
        ("XCME.WY4.23JUL25.111:25.C", "xcme", "bloomberg", "Wednesday Call"),
        ("XCME.HY4.24JUL25.111.P", "xcme", "bloomberg", "Thursday Put"),
        ("XCME.ZN1.01AUG25.111:5.C", "xcme", "bloomberg", "Friday Call"),
        ("XCME.OZN.AUG25.111:25.C", "xcme", "bloomberg", "Quarterly Call"),
        
        # Bloomberg to XCME
        ("VBYN25C3 111.750 Comdty", "bloomberg", "xcme", "Bloomberg to XCME"),
        ("1MQ5P 111.500 Comdty", "bloomberg", "xcme", "Friday Bloomberg to XCME"),
        ("TYQ5C 111.250 Comdty", "bloomberg", "xcme", "Quarterly Bloomberg to XCME"),
        
        # CME to Bloomberg
        ("VY3N5 C11175", "cme", "bloomberg", "CME to Bloomberg"),
        ("OZNQ5 P11050", "cme", "bloomberg", "Quarterly CME to Bloomberg"),
    ]
    
    for symbol, from_fmt, to_fmt, desc in test_cases:
        result = translator.translate(symbol, from_fmt, to_fmt)
        print(f"\n{desc}:")
        print(f"  Input ({from_fmt}): {symbol}")
        print(f"  Output ({to_fmt}): {result}")
        
        if result and from_fmt != to_fmt:
            # Test round trip
            back = translator.translate(result, to_fmt, from_fmt)
            print(f"  Round trip: {back}")
            if back == symbol:
                print("  ✓ Round trip successful")
            else:
                print("  ✗ Round trip failed!")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")
    
    translator = CentralizedSymbolTranslator()
    
    # Invalid symbols
    invalid_cases = [
        ("INVALID", "xcme", "bloomberg", "Invalid XCME format"),
        ("XCME.XXX.01JAN99.100.C", "xcme", "bloomberg", "Unknown symbol"),
    ]
    
    for symbol, from_fmt, to_fmt, desc in invalid_cases:
        result = translator.translate(symbol, from_fmt, to_fmt)
        print(f"\n{desc}:")
        print(f"  Input: {symbol}")
        print(f"  Result: {result}")


def test_real_database_symbols():
    """Test with symbols from actual database."""
    print("\n=== Testing Real Database Symbols ===")
    
    translator = CentralizedSymbolTranslator()
    
    # These are actual symbols from your database
    real_symbols = [
        # From spot risk (XCME format)
        ("XCME.VY3.21JUL25.111.C", "xcme", "bloomberg"),
        ("XCME.GY4.22JUL25.111.C", "xcme", "bloomberg"),
        ("XCME.WY4.23JUL25.111.C", "xcme", "bloomberg"),
        
        # From Flash/Prior (Bloomberg format)
        ("VBYN25C3 111.000 Comdty", "bloomberg", "xcme"),
        ("TJPN25C4 111.000 Comdty", "bloomberg", "xcme"),
        ("TYWN25C4 111.000 Comdty", "bloomberg", "xcme"),
        ("3MN5C 111.000 Comdty", "bloomberg", "xcme"),
    ]
    
    for symbol, from_fmt, to_fmt in real_symbols:
        result = translator.translate(symbol, from_fmt, to_fmt)
        print(f"\n{symbol}:")
        print(f"  → {result}")


def main():
    """Run all tests."""
    print("Centralized Symbol Translator Test Suite")
    print("=" * 50)
    
    try:
        test_strike_converter()
        test_symbol_translations()
        test_edge_cases()
        test_real_database_symbols()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 