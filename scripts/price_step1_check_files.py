"""Price Step 1: Check what price files exist."""

import os
from datetime import datetime

print("=== PRICE STEP 1: CHECKING PRICE FILES ===")
print(f"Time: {datetime.now()}\n")

# Check futures directory
futures_dir = "data/input/market_prices/futures"
print(f"1. FUTURES PRICE FILES ({futures_dir}):")
if os.path.exists(futures_dir):
    files = sorted([f for f in os.listdir(futures_dir) if f.endswith('.csv')])
    print(f"   Found {len(files)} files:")
    for f in files:
        path = os.path.join(futures_dir, f)
        size = os.path.getsize(path)
        print(f"   ✓ {f} ({size} bytes)")
else:
    print("   ❌ Directory does not exist!")

# Check options directory  
options_dir = "data/input/market_prices/options"
print(f"\n2. OPTIONS PRICE FILES ({options_dir}):")
if os.path.exists(options_dir):
    files = sorted([f for f in os.listdir(options_dir) if f.endswith('.csv')])
    print(f"   Found {len(files)} files:")
    for f in files:
        path = os.path.join(options_dir, f)
        size = os.path.getsize(path)
        print(f"   ✓ {f} ({size} bytes)")
else:
    print("   ❌ Directory does not exist!")

# Show sample content from each type
print("\n3. SAMPLE CONTENT:")

# Sample from futures
if os.path.exists(futures_dir):
    futures_files = sorted([f for f in os.listdir(futures_dir) if f.endswith('.csv')])
    if futures_files:
        sample_file = os.path.join(futures_dir, futures_files[0])
        print(f"\n   From {futures_files[0]}:")
        with open(sample_file, 'r') as f:
            lines = f.readlines()
            print(f"   Headers: {lines[0].strip()}")
            if len(lines) > 1:
                print(f"   First row: {lines[1].strip()}")

# Sample from options
if os.path.exists(options_dir):
    options_files = sorted([f for f in os.listdir(options_dir) if f.endswith('.csv')])
    if options_files:
        sample_file = os.path.join(options_dir, options_files[0])
        print(f"\n   From {options_files[0]}:")
        with open(sample_file, 'r') as f:
            lines = f.readlines()
            print(f"   Headers: {lines[0].strip()}")
            if len(lines) > 1:
                print(f"   First row: {lines[1].strip()}")

print("\n✅ PRICE STEP 1 COMPLETE") 