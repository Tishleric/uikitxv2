#!/usr/bin/env python
"""
Test runner for FIFO P&L calculation tests.

Usage:
    python scripts/run_fifo_pnl_tests.py [unit|integration|all]
"""

import sys
import unittest
import os
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def run_unit_tests():
    """Run unit tests for FIFO P&L calculations"""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS FOR FIFO P&L CALCULATIONS")
    print("="*60 + "\n")
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_fifo_pnl_calculations.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests for FIFO P&L with positions aggregator"""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS FOR FIFO P&L")
    print("="*60 + "\n")
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests', 'integration')
    suite = loader.discover(start_dir, pattern='test_fifo_pnl_integration.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def print_test_summary(unit_success, integration_success):
    """Print summary of test results"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Unit Tests: {'PASSED' if unit_success else 'FAILED'}")
    print(f"Integration Tests: {'PASSED' if integration_success else 'FAILED'}")
    
    if unit_success and integration_success:
        print("\nAll tests passed! ✓")
    else:
        print("\nSome tests failed. Please review the output above.")
    print("="*60 + "\n")


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = 'all'
    
    unit_success = True
    integration_success = True
    
    if test_type in ['unit', 'all']:
        unit_success = run_unit_tests()
    
    if test_type in ['integration', 'all']:
        integration_success = run_integration_tests()
    
    if test_type == 'all':
        print_test_summary(unit_success, integration_success)
    
    # Exit with appropriate code
    if unit_success and integration_success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()