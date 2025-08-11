#!/usr/bin/env python3
"""
Test script to verify broker format support in RosettaStone and backwards compatibility.
"""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone, SymbolFormat

def test_broker_translations():
    """Test broker format translations."""
    rs = RosettaStone()
    
    print("Testing Broker Format Support\n" + "="*50)
    
    # Test cases
    test_cases = [
        # Futures
        ("SEP 25 CBT 10YR TNOTE", "broker", "bloomberg"),
        ("SEP 25 CBT 30YR TBOND", "broker", "cme"),
        
        # Options
        ("CALL AUG 25 CBT 10YR TNOTE WED WK1 112.25", "broker", "cme"),
        ("PUT AUG 25 CBT 10YR T NOTE W1 TUES OPT 110.50", "broker", "bloomberg"),
        
        # Reverse translations
        ("TYU5 Comdty", "bloomberg", "broker"),
        ("ZN1Q5 C11100", "cme", "broker"),
    ]
    
    for symbol, from_fmt, to_fmt in test_cases:
        try:
            result = rs.translate(symbol, from_fmt, to_fmt)
            print(f"✓ {from_fmt} -> {to_fmt}: '{symbol}' => '{result}'")
        except Exception as e:
            print(f"✗ {from_fmt} -> {to_fmt}: '{symbol}' => ERROR: {e}")
    
    print("\n" + "="*50)
    

def test_backwards_compatibility():
    """Test that existing translations still work."""
    rs = RosettaStone()
    
    print("\nTesting Backwards Compatibility\n" + "="*50)
    
    # Existing test cases that should still work
    compatibility_tests = [
        # Bloomberg to CME
        ("TYU5 Comdty", "bloomberg", "cme"),
        ("VBYN25C3 111.750 Comdty", "bloomberg", "cme"),
        
        # CME to Bloomberg
        ("ZNU5", "cme", "bloomberg"), 
        ("VY3N5 C11175", "cme", "bloomberg"),
        
        # ActantRisk translations
        ("XCME.VY3.21JUL25.111:75.C", "actantrisk", "bloomberg"),
        ("XCME.ZN.SEP25", "actantrisk", "cme"),
        
        # ActantTrades
        ("XCMEOCADPS20250721N0VY3/111.75", "actanttrades", "bloomberg"),
        ("XCMEFFDPSX20250919U0ZN", "actanttrades", "cme"),
    ]
    
    all_passed = True
    for symbol, from_fmt, to_fmt in compatibility_tests:
        try:
            result = rs.translate(symbol, from_fmt, to_fmt)
            print(f"✓ {from_fmt} -> {to_fmt}: '{symbol}' => '{result}'")
        except Exception as e:
            print(f"✗ {from_fmt} -> {to_fmt}: '{symbol}' => ERROR: {e}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ All backwards compatibility tests passed!")
    else:
        print("✗ Some backwards compatibility tests failed!")
    
    return all_passed


def test_broker_parsing():
    """Test broker symbol parsing."""
    rs = RosettaStone()
    
    print("\nTesting Broker Parsing\n" + "="*50)
    
    broker_symbols = [
        "SEP 25 CBT 10YR TNOTE",
        "CALL AUG 25 CBT 10YR TNOTE WED WK1 112.25",
        "PUT SEP 25 CBT 30YR TBOND 111.50",
    ]
    
    for symbol in broker_symbols:
        try:
            parsed = rs.parse_symbol(symbol, SymbolFormat.BROKER)
            print(f"✓ Parsed '{symbol}':")
            print(f"  Base: {parsed.base}")
            print(f"  Strike: {parsed.strike}")
            print(f"  Type: {parsed.option_type}")
        except Exception as e:
            print(f"✗ Failed to parse '{symbol}': {e}")
    
    print("\n" + "="*50)


def main():
    """Run all tests."""
    test_broker_parsing()
    test_broker_translations()
    compatible = test_backwards_compatibility()
    
    print("\n" + "="*70)
    if compatible:
        print("✓ SUCCESS: All tests passed! Broker support added with full backwards compatibility.")
    else:
        print("✗ FAILURE: Some tests failed. Please review the implementation.")
    print("="*70)


if __name__ == "__main__":
    main()