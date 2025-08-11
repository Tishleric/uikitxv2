"""
Runner script for unrealized P&L accuracy test
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Change to project root directory
os.chdir(project_root)

# Import and run the test
from tests.test_unrealized_pnl_production_fidelity import TestUnrealizedPnLAccuracy

if __name__ == "__main__":
    print(f"Working directory: {os.getcwd()}")
    print(f"Database path will be: {os.path.join(os.getcwd(), 'trades_test_copy.db')}")
    
    # Run the test
    tester = TestUnrealizedPnLAccuracy()
    tester.run_all_tests()