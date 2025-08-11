#!/usr/bin/env python3
"""Test with actual broker symbols from the calendar."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

# Create fresh instance
print("Creating RosettaStone instance...")
rs = RosettaStone()

print("\nBROKER TO BLOOMBERG CONVERSION TEST")
print("="*70)

# Test with actual symbols that should exist based on calendar
test_cases = [
    # Futures (these work)
    ("SEP 25 CBT 10YR TNOTE", "Future - Sept 10Y"),
    
    # Options - based on what's in calendar
    ("CALL JUL 25 CBT 10YR TNOTE 111.00", "Monday Weekly Call"),
    ("PUT JUL 25 CBT 10YR TNOTE 111.00", "Monday Weekly Put"),
    ("CALL JUL 25 CBT 10YR TNOTE W4 TUES OPT 111.00", "Tuesday Week 4 Call"),
    ("CALL AUG 25 CBT 10YR TNOTE WKLY WK1 112.25", "Friday Week 1 Call"),
]

for symbol, desc in test_cases:
    print(f"\nTest: {desc}")
    print(f"Input:  {symbol}")
    
    # Parse to see what we get
    try:
        parsed = rs.parse_symbol(symbol, rs.SymbolFormat.BROKER)
        print(f"Parsed: base='{parsed.base}', strike='{parsed.strike}', type='{parsed.option_type}'")
        
        # Check if lookup exists
        if parsed.option_type == 'F':
            lookup_key = f"broker_{parsed.base}_to_bloomberg"
        else:
            lookup_key = f"broker_{parsed.base}_to_bloomberg_{parsed.option_type}"
        
        if lookup_key in rs.lookups:
            print(f"Lookup found: {lookup_key} = {rs.lookups[lookup_key]}")
            # Try translation
            result = rs.translate(symbol, "broker", "bloomberg")
            print(f"✓ Translation: {result}")
        else:
            print(f"✗ Lookup NOT found: {lookup_key}")
            # Check similar
            similar = [k for k in rs.lookups.keys() if parsed.base[:20] in k and "broker" in k][:5]
            if similar:
                print("  Similar lookups:")
                for s in similar:
                    print(f"    {s}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

# Let's also check what broker lookups actually exist
print("\n\nACTUAL BROKER LOOKUPS (first 20):")
print("="*70)
broker_lookups = [(k, v) for k, v in rs.lookups.items() if k.startswith("broker_")]
for k, v in sorted(broker_lookups)[:20]:
    print(f"{k} = {v}")