#!/usr/bin/env python3
"""Simple test of broker translations."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

rs = RosettaStone()

# Test 1: Futures (these work)
print("FUTURES TEST:")
print("-" * 50)
future = "SEP 25 CBT 10YR TNOTE"
result = rs.translate(future, "broker", "bloomberg")
print(f"Input:  {future}")
print(f"Output: {result}")

# Test 2: Options 
print("\n\nOPTIONS TEST:")
print("-" * 50)

# Test with actual calendar entry
option1 = "CALL JUL 25 CBT 10YR TNOTE 111.00"
result1 = rs.translate(option1, "broker", "bloomberg")
print(f"Input:  {option1}")
print(f"Output: {result1}")

# Check what mapping exists
key = "broker_CALL JUL 25 CBT 10YR TNOTE 111.00_to_bloomberg"
if key in rs.lookups:
    print(f"Mapping exists: {key} = {rs.lookups[key]}")
else:
    print(f"No mapping for: {key}")
    # Check similar
    similar = [k for k in rs.lookups.keys() if "broker_CALL JUL 25 CBT 10YR TNOTE" in k and "bloomberg" in k]
    if similar:
        print("Similar mappings:")
        for s in similar[:3]:
            print(f"  {s} = {rs.lookups[s]}")

# Test reverse
print("\n\nREVERSE TEST:")
print("-" * 50)
bb = "VBYN25C3 111.00 Comdty"
result = rs.translate(bb, "bloomberg", "broker")
print(f"Input:  {bb}")
print(f"Output: {result}")

# Show reconstruction
print("\n\nRECONSTRUCTION TEST:")
print("-" * 50)
parsed = rs.parse_symbol(option1, rs.SymbolFormat.BROKER)
print(f"Parsed: base='{parsed.base}', strike='{parsed.strike}', type='{parsed.option_type}'")

# Manual lookup
lookup_key = f"broker_{parsed.base}_to_bloomberg_{parsed.option_type}"
target = rs.lookups.get(lookup_key)
print(f"Lookup key: {lookup_key}")
print(f"Target base: {target}")

if target:
    reconstructed = rs._reconstruct_symbol(target, parsed.strike, parsed.option_type, 
                                          rs.SymbolFormat.BLOOMBERG, parsed.symbol_class)
    print(f"Reconstructed: {reconstructed}")