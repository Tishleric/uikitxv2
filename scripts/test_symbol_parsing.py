#!/usr/bin/env python3
"""Test symbol parsing for specific trade ledger entries."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter

# Test symbols from the fresh trade ledger
test_symbols = [
    "XCMEFFDPSX20250919U0ZN",  # Future
    "XCMEOPADPS20250721N0VY3/111.25",  # VY3 option
    "XCMEOPADPS20250723N0WY4/111.5",   # WY4 option  
    "XCMEOPADPS20250725N0ZN4/110.75",  # ZN4 option (July 25 - Friday)
]

adapter = TradeLedgerAdapter()

print("Testing Symbol Parsing:")
print("=" * 70)

for symbol in test_symbols:
    print(f"\nInput: {symbol}")
    
    # Parse components
    components = adapter.parse_xcme_symbol(symbol)
    if components:
        print(f"  Type: {components['type']}")
        print(f"  Product: {components.get('product')}")
        if components['type'] == 'option':
            print(f"  Series: {components.get('series')}")
            print(f"  Strike: {components.get('strike')}")
    else:
        print("  ✗ Failed to parse components")
    
    # Parse to TYU5 format
    result = adapter._parse_xcme_symbol(symbol)
    if result:
        print(f"  TYU5 Symbol: {result['tyu5_symbol']}")
        print(f"  Bloomberg: {result['bloomberg_symbol']}")
    else:
        print("  ✗ Failed to create TYU5 format")

# Check July 25 specifically
print("\n" + "=" * 70)
print("July 25, 2025 Analysis:")
print("  - This is a FRIDAY, so it should be a standard quarterly option")
print("  - Expected Bloomberg format: TYQ5P (not ZN4 weekly format)")
print("  - But the trade ledger has ZN4 which suggests weekly format")
print("  - This mismatch may need special handling") 