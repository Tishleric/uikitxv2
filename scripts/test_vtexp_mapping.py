#!/usr/bin/env python
"""Test vtexp symbol mapping."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.actant.spot_risk.vtexp_mapper import VtexpSymbolMapper
from lib.trading.actant.spot_risk.time_calculator import read_vtexp_from_csv

# Test the mapping
mapper = VtexpSymbolMapper()

# Sample spot risk symbols
spot_risk_symbols = [
    "XCME.ZN2.11JUL25.110.C",
    "XCME.ZN2.11JUL25.110.5.C",
    "XCME.VY2.14JUL25.111.P",
    "XCME.WY3.16JUL25.112.C",
    "XCME.ZN3.18JUL25.113.P"
]

print("=== Testing Symbol Mapping ===")
for symbol in spot_risk_symbols:
    vtexp_base = mapper.spot_risk_to_vtexp_base(symbol)
    print(f"{symbol} -> {vtexp_base}")

# Read actual vtexp data
print("\n=== Reading vtexp CSV ===")
vtexp_dict = read_vtexp_from_csv()
print(f"Loaded {len(vtexp_dict)} vtexp entries")
print("Sample entries:")
for key, value in list(vtexp_dict.items())[:5]:
    print(f"  {key}: {value}")

# Test full mapping
print("\n=== Testing Full Mapping ===")
mapping = mapper.create_mapping_dict(spot_risk_symbols, vtexp_dict)
print(f"Mapped {len(mapping)} out of {len(spot_risk_symbols)} symbols")
for symbol, vtexp in mapping.items():
    print(f"  {symbol}: {vtexp}") 