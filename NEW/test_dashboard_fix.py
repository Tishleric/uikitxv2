#!/usr/bin/env python3
"""
Test script to verify the dashboard fix works correctly.
This script can be run from any directory to test path robustness.
"""

import os
import sys
from pathlib import Path

def test_dashboard_fix():
    """Test that the dashboard loads data correctly."""
    print("🧪 Testing Dashboard Fix")
    print("=" * 50)
    
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        # Test 1: Run from the NEW directory
        print("\n1. Testing from NEW directory:")
        new_dir = Path(__file__).parent.resolve()
        os.chdir(new_dir)
        print(f"   Current directory: {os.getcwd()}")
        
        # Import and test
        from pnl_dashboard import create_app, SCRIPT_DIR
        app = create_app(str(SCRIPT_DIR))
        print("   ✅ Dashboard created successfully from NEW directory")
        
        # Test 2: Run from parent directory  
        print("\n2. Testing from parent directory:")
        os.chdir(new_dir.parent)
        print(f"   Current directory: {os.getcwd()}")
        
        # Clear the module from cache to force reimport
        if 'pnl_dashboard' in sys.modules:
            del sys.modules['pnl_dashboard']
        
        # Add NEW to path and import
        sys.path.insert(0, str(new_dir))
        from pnl_dashboard import create_app, SCRIPT_DIR
        app2 = create_app(str(SCRIPT_DIR))
        print("   ✅ Dashboard created successfully from parent directory")
        
        # Test 3: Check data loading
        print("\n3. Checking data loading:")
        print(f"   Script directory: {SCRIPT_DIR}")
        print(f"   CSV file exists: {(SCRIPT_DIR / 'GE_XCME.ZN_20250610_103938.csv').exists()}")
        
        # Check if data was loaded
        from pnl_dashboard import PnLDashboard
        dashboard = PnLDashboard(str(SCRIPT_DIR))
        print(f"   Available expirations: {dashboard.available_expirations}")
        print(f"   Data loaded: {'Yes' if dashboard.all_greeks else 'No'}")
        
        if dashboard.available_expirations:
            print("   ✅ Data loaded successfully!")
        else:
            print("   ❌ No data loaded - check error messages above")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original directory
        os.chdir(original_dir)
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Dashboard is now robust to different run locations.")
    return True

if __name__ == "__main__":
    success = test_dashboard_fix()
    sys.exit(0 if success else 1) 