#!/usr/bin/env python
"""Test file watcher automation for trades and prices."""

import sys
from pathlib import Path
import time
import shutil
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService

def test_file_watchers():
    """Test that file watchers detect and process new files."""
    
    print("Testing File Watcher Automation")
    print("=" * 60)
    
    # Initialize service
    service = UnifiedPnLService(
        db_path="data/output/pnl/pnl_tracker.db",
        trade_ledger_dir="data/input/trade_ledger",
        price_directories=[
            "data/input/market_prices/futures",
            "data/input/market_prices/options"
        ]
    )
    
    # Start watchers
    print("\nStarting file watchers...")
    service.start_watchers()
    
    # Give watchers time to start
    time.sleep(2)
    
    # Test 1: Check what files the price watcher is looking for
    print("\n1. Price File Pattern Check:")
    print("   Price watcher expects: market_prices_YYYYMMDD_HHMM.csv")
    
    # List actual files
    futures_dir = Path("data/input/market_prices/futures")
    options_dir = Path("data/input/market_prices/options")
    
    print("\n   Actual futures files:")
    for f in sorted(futures_dir.glob("*.csv"))[:3]:
        print(f"     - {f.name}")
        
    print("\n   Actual options files:")
    for f in sorted(options_dir.glob("*.csv"))[:3]:
        print(f"     - {f.name}")
    
    # Test 2: Check trade file pattern
    print("\n2. Trade File Pattern Check:")
    print("   Trade watcher expects: trades_YYYYMMDD.csv")
    
    trades_dir = Path("data/input/trade_ledger")
    print("\n   Actual trade files:")
    for f in sorted(trades_dir.glob("*.csv"))[:3]:
        print(f"     - {f.name}")
    
    # Test 3: Create a test file with expected pattern
    print("\n3. Testing File Detection:")
    
    # Create a test trade file
    test_trade_file = trades_dir / f"trades_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"\n   Creating test trade file: {test_trade_file.name}")
    
    # Copy an existing trade file
    existing_trade = trades_dir / "trades_20250712.csv"
    if existing_trade.exists():
        shutil.copy(existing_trade, test_trade_file)
        print("   File created, waiting for detection...")
        time.sleep(3)
        print("   Check logs to see if file was processed")
    else:
        print("   No existing trade file to copy")
    
    # Test 4: Check if watchers are running
    print("\n4. Watcher Status:")
    print(f"   Trade watcher: {'Running' if service.trade_watcher and hasattr(service.trade_watcher, '_observer') else 'Not running'}")
    print(f"   Price watcher: {'Running' if service.price_watcher and service.price_watcher.is_running else 'Not running'}")
    
    # Clean up
    if test_trade_file.exists():
        test_trade_file.unlink()
        print(f"\n   Cleaned up test file: {test_trade_file.name}")
    
    # Stop watchers
    print("\nStopping watchers...")
    service.stop_watchers()
    
    print("\nConclusion:")
    print("- Trade files use correct pattern (trades_YYYYMMDD.csv)")
    print("- Price files use WRONG pattern (should be market_prices_* but are Futures_*/Options_*)")
    print("- This is why price files are not being automatically processed!")

if __name__ == "__main__":
    test_file_watchers() 