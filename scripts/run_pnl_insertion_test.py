"""
Runner script for P&L insertion pipeline test
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Change to project root directory
os.chdir(project_root)

# Import and run the test
from tests.test_pnl_insertion_pipeline import TestPnLInsertionPipeline

if __name__ == "__main__":
    print(f"Working directory: {os.getcwd()}")
    print("Starting P&L insertion pipeline test...\n")
    
    try:
        test = TestPnLInsertionPipeline()
        test.test_pnl_insertion_pipeline()
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()