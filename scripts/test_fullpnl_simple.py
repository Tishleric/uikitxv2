#!/usr/bin/env python3
"""Simple test of FULLPNL rebuild."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.fullpnl import FULLPNLBuilder
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(message)s')

print("Starting FULLPNL rebuild test...")
print("=" * 50)

# Initialize builder
builder = FULLPNLBuilder()

# Perform rebuild
print("\nRebuilding FULLPNL table...")
results = builder.build_or_update(full_rebuild=True)

print(f"\nRebuild results:")
for key, value in results.items():
    print(f"  {key}: {value}")

# Get summary
summary = builder.get_table_summary()
print(f"\nTable summary:")
print(f"  Total symbols: {summary['total_symbols']}")
print(f"  With Greeks: {summary.get('with_delta_f', 0)}")
print(f"  With bid/ask: {summary.get('with_bid', 0)}")

# Show sample data
print("\nSample data:")
cursor = builder.pnl_db.execute("""
    SELECT symbol, delta_f, bid, ask 
    FROM FULLPNL 
    WHERE delta_f IS NOT NULL OR bid IS NOT NULL
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: delta_f={row[1]}, bid={row[2]}, ask={row[3]}")

builder.close()
print("\nDone!") 