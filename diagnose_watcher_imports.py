#!/usr/bin/env python3
"""
Diagnose import issues with file watchers
"""

import sys
import traceback
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Diagnosing Watcher Import Issues")
print("=" * 60)

# Test 1: Check if watchdog is installed
print("\n1. Testing watchdog package:")
try:
    import watchdog
    print("✓ watchdog is installed")
    try:
        print(f"  Version: {watchdog.__version__}")
    except AttributeError:
        print("  (version info not available)")
except ImportError as e:
    print("✗ watchdog is NOT installed")
    print(f"  Error: {e}")
    print("\n  To fix: pip install watchdog")

# Test 2: Check individual imports
print("\n2. Testing individual imports:")

# Test update_current_price
try:
    from lib.trading.pnl_fifo_lifo.data_manager import update_current_price
    print("✓ update_current_price imported successfully")
except Exception as e:
    print("✗ Failed to import update_current_price")
    print(f"  Error: {e}")
    traceback.print_exc()

# Test 3: Check RosettaStone
print("\n3. Testing RosettaStone import:")
try:
    sys.path.append(str(Path(__file__).parent / "lib" / "trading"))
    from market_prices.rosetta_stone import RosettaStone
    print("✓ RosettaStone imported successfully")
except Exception as e:
    print("✗ Failed to import RosettaStone")
    print(f"  Error: {e}")
    print("  This is used by trade_ledger_watcher.py")

# Test 4: Try importing watchers with detailed errors
print("\n4. Testing watcher imports:")

print("\n4a. SpotRiskPriceWatcher:")
try:
    from lib.trading.pnl_fifo_lifo.spot_risk_price_watcher import SpotRiskPriceWatcher
    print("✓ SpotRiskPriceWatcher imported successfully")
except Exception as e:
    print("✗ Failed to import SpotRiskPriceWatcher")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error: {e}")
    traceback.print_exc()

print("\n4b. TradeLedgerWatcher:")
try:
    from lib.trading.pnl_fifo_lifo.trade_ledger_watcher import TradeLedgerWatcher
    print("✓ TradeLedgerWatcher imported successfully")
except Exception as e:
    print("✗ Failed to import TradeLedgerWatcher")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error: {e}")
    traceback.print_exc()

# Test 5: Check __init__.py imports
print("\n5. Testing module __init__.py imports:")
try:
    import lib.trading.pnl_fifo_lifo
    print("✓ Module imported successfully")
    print(f"  Available exports: {[x for x in dir(lib.trading.pnl_fifo_lifo) if not x.startswith('_')]}")
except Exception as e:
    print("✗ Failed to import module")
    print(f"  Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnosis complete!")
print("=" * 60) 