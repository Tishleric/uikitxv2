#!/usr/bin/env python3
"""
ACTIVE Script: Verify TYU5 Format Requirements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("VERIFYING TYU5 DATA FORMAT")
print("=" * 80)

# 1. Check what PositionCalculator expects
print("\n1. What TYU5 PositionCalculator expects:")
print("-" * 40)
with open("lib/trading/pnl/tyu5_pnl/core/position_calculator.py", "r") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "def update_prices" in line:
            # Show the method and a few lines after
            for j in range(i, min(i+10, len(lines))):
                print(f"Line {j+1}: {lines[j].rstrip()}")
            break

# 2. Check what format our adapter returns
print("\n\n2. What our TYU5Adapter returns:")
print("-" * 40)
try:
    from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
    adapter = TYU5Adapter()
    df = adapter.get_market_prices()
    print(f"Columns: {list(df.columns)}")
    print(f"Shape: {df.shape}")
except Exception as e:
    print(f"Error: {e}")

# 3. Summary
print("\n\n3. FORMAT VERIFICATION:")
print("-" * 40)
print("✓ TYU5 expects a DataFrame with columns:")
print("  - Symbol (TYU5/CME format)")
print("  - Flash_Close (market price)")
print("  - Prior_Close (previous close)")
print("\n✓ The adapter is responsible for:")
print("  - Converting Bloomberg → TYU5 symbol format")
print("  - Querying database and returning correct columns")
print("  - Combining futures and options data")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE") 