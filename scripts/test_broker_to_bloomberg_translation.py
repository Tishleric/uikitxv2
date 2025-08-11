#!/usr/bin/env python3
"""
Test broker to bloomberg translations - the most critical conversion path.
"""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_broker_to_bloomberg():
    """Test broker format to bloomberg translations."""
    rs = RosettaStone()
    
    print("Testing Broker → Bloomberg Translations")
    print("=" * 60)
    
    # Test cases based on actual broker trades from the DASONLY files
    test_cases = [
        # Futures
        ("SEP 25 CBT 10YR TNOTE", "TYU5 Comdty"),
        ("SEP 25 CBT 30YR TBOND", None),  # Not in calendar, should fail gracefully
        
        # Options - these are the actual formats from broker trades
        ("CALL AUG 25 CBT 10YR TNOTE WKLY WK1 112.25", None),  # Test actual format
        ("CALL AUG 25 CBT 10YR TNOTE WED WK1 112.25", None),
        ("PUT AUG 25 CBT 10YR T NOTE W1 TUES OPT 110.50", None),
        
        # Test with specific strikes that exist in calendar
        ("CALL JUL 25 CBT 10YR TNOTE 111.00", "TYN5C111 Comdty"),
        ("PUT JUL 25 CBT 10YR TNOTE 111.00", "TYN5P111 Comdty"),
        
        # Weekly options
        ("CALL JUL 25 CBT 10YR TNOTE W4 TUES OPT 111.00", None),
        ("CALL JUL 25 CBT 10YR TNOTE WED WK4 111.00", None),
    ]
    
    success_count = 0
    fail_count = 0
    
    for broker_symbol, expected_bloomberg in test_cases:
        try:
            result = rs.translate(broker_symbol, "broker", "bloomberg")
            if result:
                print(f"✓ {broker_symbol}")
                print(f"  → {result}")
                if expected_bloomberg and result != expected_bloomberg:
                    print(f"  ⚠ Expected: {expected_bloomberg}")
                success_count += 1
            else:
                print(f"✗ {broker_symbol}")
                print(f"  → Translation not found")
                fail_count += 1
        except Exception as e:
            print(f"✗ {broker_symbol}")
            print(f"  → Error: {e}")
            fail_count += 1
        print()
    
    print(f"\nSummary: {success_count} successful, {fail_count} failed")
    
    # Test reverse translations (Bloomberg → Broker)
    print("\n" + "="*60)
    print("Testing Bloomberg → Broker Translations")
    print("="*60)
    
    bloomberg_tests = [
        "TYU5 Comdty",
        "TYN5C111 Comdty",
        "TYN5P111 Comdty",
    ]
    
    for bloomberg_symbol in bloomberg_tests:
        try:
            result = rs.translate(bloomberg_symbol, "bloomberg", "broker")
            if result:
                print(f"✓ {bloomberg_symbol} → {result}")
            else:
                print(f"✗ {bloomberg_symbol} → Translation not found")
        except Exception as e:
            print(f"✗ {bloomberg_symbol} → Error: {e}")
    
    return success_count, fail_count


if __name__ == "__main__":
    test_broker_to_bloomberg()