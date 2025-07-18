#!/usr/bin/env python3
"""Quick check of FULLPNL table status."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.fullpnl import FULLPNLBuilder

builder = FULLPNLBuilder()
summary = builder.get_table_summary()

print("\nFULLPNL Table Summary:")
print("=" * 50)

# Basic counts
for key, value in sorted(summary.items()):
    if not key.endswith('_coverage'):
        print(f"{key:20}: {value}")

print("\nCoverage Percentages:")
print("-" * 50)
for key, value in sorted(summary.items()):
    if key.endswith('_coverage'):
        print(f"{key:20}: {value}%")

# Show sample data
print("\nSample Data (first 5 rows):")
print("-" * 50)
cursor = builder.pnl_db.execute("""
    SELECT symbol, open_position, bid, ask, delta_f
    FROM FULLPNL
    ORDER BY symbol
    LIMIT 5
""")

for row in cursor.fetchall():
    symbol, pos, bid, ask, delta = row
    print(f"{symbol:25} pos={pos:6} bid={bid} ask={ask} delta_f={delta}")

builder.close()
print("\nDone!") 