"""Step 1: Check trade CSV files in input folder."""

import os
from datetime import datetime

print("=== STEP 1: CHECKING TRADE FILES ===")
print(f"Time: {datetime.now()}\n")

trade_dir = "data/input/trade_ledger"
print(f"Looking in: {trade_dir}")

# Get all CSV files
all_files = os.listdir(trade_dir)
csv_files = [f for f in all_files if f.endswith('.csv')]
trade_files = [f for f in csv_files if f.startswith('trades_')]

print(f"\nFound {len(trade_files)} trade files:")
for f in sorted(trade_files):
    path = os.path.join(trade_dir, f)
    size = os.path.getsize(path)
    # Count lines
    with open(path, 'r') as file:
        lines = len(file.readlines())
    print(f"  ✓ {f} - {size} bytes, {lines} lines")

# Show sample content from each file
print("\nSample content from each file:")
for f in sorted(trade_files):
    path = os.path.join(trade_dir, f)
    print(f"\n--- {f} ---")
    with open(path, 'r') as file:
        lines = file.readlines()
        print(f"Headers: {lines[0].strip()}")
        if len(lines) > 1:
            print(f"First trade: {lines[1].strip()}")
        if len(lines) > 2:
            print(f"Second trade: {lines[2].strip()}")

print("\n✅ STEP 1 COMPLETE: Trade files found and readable") 