#!/usr/bin/env python
"""
Quick test runner for the TradeLedgerWatcher realized P&L test.

This demonstrates how the TradeLedgerWatcher processes trades:
1. Reads trades from CSV files
2. Translates symbols from Actant to Bloomberg format
3. Calculates FIFO realized P&L
4. Updates the database tables

Usage:
    python scripts/test_realized_pnl_mimicking_watcher.py
"""

import sys
import os
import unittest

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the test
from tests.test_trade_ledger_watcher_realized_pnl import TestTradeLedgerWatcherRealizedPnL


def main():
    """Run the test and show detailed output"""
    print("="*60)
    print("Testing FIFO Realized P&L (Mimicking TradeLedgerWatcher)")
    print("="*60)
    print()
    print("This test demonstrates the exact process used by TradeLedgerWatcher:")
    print("1. Read trades from CSV")
    print("2. Translate symbols (Actant -> Bloomberg)")
    print("3. Process through FIFO engine")
    print("4. Calculate realized P&L")
    print("5. Update database tables")
    print()
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTradeLedgerWatcherRealizedPnL)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\nAll tests passed! ✓")
        print("\nThe TradeLedgerWatcher correctly:")
        print("- Processes trades from CSV files")
        print("- Calculates FIFO realized P&L")
        print("- Handles partial fills")
        print("- Updates daily positions")
        print("- Manages multiple symbols")
    else:
        print("\nSome tests failed. Review the output above.")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())