#!/usr/bin/env python3
"""Final test of broker translations with strike-less calendar."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

# Reload rosetta stone to pick up new calendar
rs = RosettaStone()

print("BROKER TRANSLATION TEST - FINAL")
print("="*70)

# Test cases
test_cases = [
    # Futures
    ("SEP 25 CBT 10YR TNOTE", "broker", "bloomberg", "Future"),
    ("SEP 25 CBT 30YR TBOND", "broker", "bloomberg", "Future"),
    
    # Options - with strikes and product variations
    ("CALL JUL 25 CBT 10YR TNOTE 111.00", "broker", "bloomberg", "Monday Weekly"),
    ("PUT JUL 25 CBT 10YR TNOTE 112.50", "broker", "bloomberg", "Monday Weekly"),
    ("CALL AUG 25 CBT 10YR TNOTE WKLY WK1 112.25", "broker", "bloomberg", "Friday Weekly"),
    ("CALL AUG 25 CBT 10YR T NOTE WED WK1 112.25", "broker", "bloomberg", "Wednesday Weekly (with space)"),
    ("PUT AUG 25 CBT 10YR T NOTE W1 TUES OPT 110.50", "broker", "bloomberg", "Tuesday Weekly (with space)"),
]

for symbol, from_fmt, to_fmt, desc in test_cases:
    print(f"\nTest: {desc}")
    print(f"Input:  {symbol}")
    
    try:
        result = rs.translate(symbol, from_fmt, to_fmt)
        if result:
            print(f"✓ Output: {result}")
        else:
            print(f"✗ Translation failed")
    except Exception as e:
        print(f"✗ Error: {e}")

# Test reverse translations
print("\n\nREVERSE TRANSLATIONS:")
print("="*70)

reverse_tests = [
    ("TYU5 Comdty", "bloomberg", "broker", "Sept Futures"),
    ("VBYN25C3 111.00 Comdty", "bloomberg", "broker", "Monday Weekly Call"),
    ("TJPN25P4 110.50 Comdty", "bloomberg", "broker", "Tuesday Weekly Put"),
]

for symbol, from_fmt, to_fmt, desc in reverse_tests:
    print(f"\nTest: {desc}")
    print(f"Input:  {symbol}")
    
    try:
        result = rs.translate(symbol, from_fmt, to_fmt)
        if result:
            print(f"✓ Output: {result}")
        else:
            print(f"✗ Translation failed")
    except Exception as e:
        print(f"✗ Error: {e}")

# Show some actual lookups
print("\n\nSAMPLE LOOKUPS:")
print("="*70)
sample_keys = [
    "broker_CALL JUL 25 CBT 10YR TNOTE_to_bloomberg_C",
    "broker_PUT JUL 25 CBT 10YR TNOTE_to_bloomberg_P",
    "broker_SEP 25 CBT 10YR TNOTE_to_bloomberg",
]

for key in sample_keys:
    if key in rs.lookups:
        print(f"✓ {key} = {rs.lookups[key]}")
    else:
        print(f"✗ {key} NOT FOUND")