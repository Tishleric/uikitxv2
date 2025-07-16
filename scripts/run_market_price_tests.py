#!/usr/bin/env python3
"""
Run all market price integration tests.

This script runs the comprehensive test suite for the market price processing system.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Running Market Price Integration Tests")
    print("=" * 60)
    
    # Test files to run
    test_files = [
        "tests/integration/test_market_prices_core.py",
        "tests/integration/test_market_prices_monitor.py",
        "tests/integration/test_market_prices_errors.py"
    ]
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("ERROR: pytest not installed. Please install with: pip install pytest")
        return 1
    
    # Run tests with verbose output
    test_args = [
        "-v",  # Verbose
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
    ]
    
    # Add test files
    test_args.extend([str(project_root / f) for f in test_files])
    
    # Run pytest
    print(f"\nRunning: pytest {' '.join(test_args)}")
    result = pytest.main(test_args)
    
    if result == 0:
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Some tests failed! ❌")
        print("=" * 60)
    
    return result

def run_single_test_demo():
    """Run a single test to demonstrate functionality."""
    print("\n" + "=" * 60)
    print("Running Single Test Demo")
    print("=" * 60)
    
    # Import and run a basic test
    from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor
    from datetime import datetime, date
    import tempfile
    import pandas as pd
    
    print("\n1. Creating temporary database...")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    storage = MarketPriceStorage(db_path=db_path)
    processor = FuturesProcessor(storage)
    
    print("2. Creating test futures file...")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create 2pm file
        filepath = Path(temp_dir) / 'Futures_20250715_1400.csv'
        data = {
            'SYMBOL': ['TU', 'FV', 'TY', 'US', 'RX'],
            'PX_LAST': [110.5, 108.25, 115.75, 112.0, 140.5],
            'PX_SETTLE': [110.75, 108.5, 116.0, 112.25, 140.75]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
        print(f"3. Processing file: {filepath.name}")
        result = processor.process_file(filepath)
        print(f"   Result: {result}")
        
        print("\n4. Checking database...")
        futures_data = storage.get_futures_prices(date(2025, 7, 15))
        print(f"   Stored {len(futures_data)} symbols")
        
        print("\n5. Sample data:")
        for row in futures_data[:3]:
            print(f"   {row['symbol']}: current_price={row.get('current_price', 'NULL')}")
        
        # Create 4pm file
        print("\n6. Creating 4pm file...")
        filepath2 = Path(temp_dir) / 'Futures_20250715_1600.csv'
        df.to_csv(filepath2, index=False)
        
        result2 = processor.process_file(filepath2)
        print(f"   Result: {result2}")
        
        print("\n7. Checking next day's prior close...")
        futures_next = storage.get_futures_prices(date(2025, 7, 16))
        if futures_next:
            print(f"   July 16 has {len(futures_next)} prior close entries")
            sample = futures_next[0]
            print(f"   {sample['symbol']}: prior_close={sample.get('prior_close', 'NULL')}")
    
    # Cleanup
    db_path.unlink()
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run market price integration tests")
    parser.add_argument("--demo", action="store_true", help="Run demo only")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    
    args = parser.parse_args()
    
    if args.demo:
        run_single_test_demo()
    elif args.full:
        sys.exit(run_tests())
    else:
        # Default: run demo
        print("Running demo by default. Use --full for complete test suite.")
        run_single_test_demo() 