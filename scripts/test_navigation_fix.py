#!/usr/bin/env python
"""Test that the navigation callback parameters match the inputs"""

import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.dashboards.main.app import handle_navigation
import inspect

def test_navigation_parameters():
    """Check that handle_navigation has the correct number of parameters"""
    
    # Get the function signature
    sig = inspect.signature(handle_navigation)
    params = list(sig.parameters.keys())
    
    print(f"handle_navigation parameters ({len(params)} total):")
    for i, param in enumerate(params, 1):
        print(f"  {i}. {param}")
    
    # Expected parameters
    expected_params = [
        'pm_clicks',
        'analysis_clicks', 
        'greek_clicks',
        'logs_clicks',
        'project_docs_clicks',
        'scenario_ladder_clicks',
        'actant_eod_clicks',
        'actant_pnl_clicks',
        'pnl_tracking_clicks',
        'pnl_tracking_v2_clicks',  # The newly added parameter
        'spot_risk_clicks',
        'observatory_clicks',
        'current_page'
    ]
    
    print(f"\nExpected {len(expected_params)} parameters")
    
    # Check if they match
    if params == expected_params:
        print("\n[SUCCESS] Parameters match perfectly!")
        print("The navigation callback now has the correct number of parameters.")
        return True
    else:
        print("\n[ERROR] Parameter mismatch!")
        print("\nExpected:")
        for i, param in enumerate(expected_params, 1):
            print(f"  {i}. {param}")
        return False

if __name__ == "__main__":
    success = test_navigation_parameters()
    sys.exit(0 if success else 1) 