#!/usr/bin/env python3
"""Debug broker lookup creation in rosetta stone."""

import sys
sys.path.insert(0, '.')

# Temporarily patch the RosettaStone to add debug output
import lib.trading.market_prices.rosetta_stone as rs_module

# Store original method
original_build_lookups = rs_module.RosettaStone._build_lookups

def debug_build_lookups(self):
    """Wrapped version with debug output."""
    print("DEBUG: Building lookups...")
    
    # Call original
    original_build_lookups(self)
    
    # Count broker lookups
    broker_lookups = [(k, v) for k, v in self.lookups.items() if 'broker' in k]
    print(f"DEBUG: Total broker lookups created: {len(broker_lookups)}")
    
    # Show some samples
    print("\nDEBUG: Sample broker lookups (first 10):")
    for k, v in sorted(broker_lookups)[:10]:
        print(f"  {k} = {v}")
    
    # Check specific ones we expect
    expected = [
        "broker_CALL JUL 25 CBT 10YR TNOTE_to_bloomberg_C",
        "broker_PUT JUL 25 CBT 10YR TNOTE_to_bloomberg_P",
        "broker_SEP 25 CBT 10YR TNOTE_to_bloomberg"
    ]
    
    print("\nDEBUG: Checking expected lookups:")
    for key in expected:
        if key in self.lookups:
            print(f"  ✓ {key} = {self.lookups[key]}")
        else:
            print(f"  ✗ {key} NOT FOUND")

# Monkey patch
rs_module.RosettaStone._build_lookups = debug_build_lookups

# Now create RosettaStone
from lib.trading.market_prices.rosetta_stone import RosettaStone

print("Creating RosettaStone instance...")
rs = RosettaStone()

# Test translation
print("\n\nTEST TRANSLATIONS:")
print("="*50)

# Future
result = rs.translate("SEP 25 CBT 10YR TNOTE", "broker", "bloomberg")
print(f"SEP 25 CBT 10YR TNOTE -> {result}")

# Option
result = rs.translate("CALL JUL 25 CBT 10YR TNOTE 111.00", "broker", "bloomberg")
print(f"CALL JUL 25 CBT 10YR TNOTE 111.00 -> {result}")