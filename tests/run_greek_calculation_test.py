"""
Run specific Greek calculation test with detailed output.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from test_spot_risk_greek_calculations import TestSpotRiskGreekCalculations

if __name__ == "__main__":
    # Create test suite with specific test
    suite = unittest.TestSuite()
    
    # Add specific tests to run
    suite.addTest(TestSpotRiskGreekCalculations('test_2_greek_calculation_results'))
    
    # Run with high verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)