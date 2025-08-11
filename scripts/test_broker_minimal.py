#!/usr/bin/env python3
"""Minimal broker test."""

import sys
sys.path.insert(0, '.')
from lib.trading.market_prices.rosetta_stone import RosettaStone

rs = RosettaStone()

# Test 1: Future
print("TEST 1: Future")
result = rs.translate("SEP 25 CBT 10YR TNOTE", "broker", "bloomberg")
print(f"SEP 25 CBT 10YR TNOTE -> {result}")

# Test 2: Option
print("\nTEST 2: Option")
result = rs.translate("CALL JUL 25 CBT 10YR TNOTE 111.00", "broker", "bloomberg")
print(f"CALL JUL 25 CBT 10YR TNOTE 111.00 -> {result}")

# Check if lookup exists
key = "broker_CALL JUL 25 CBT 10YR TNOTE_to_bloomberg_C"
exists = key in rs.lookups
print(f"\nLookup exists: {exists}")
if exists:
    print(f"Value: {rs.lookups[key]}")

# Show first few broker lookups
print("\nFirst 5 broker option lookups:")
broker_opts = [(k, v) for k, v in rs.lookups.items() if k.startswith("broker_CALL") and "bloomberg" in k]
for k, v in broker_opts[:5]:
    print(f"{k} = {v}")