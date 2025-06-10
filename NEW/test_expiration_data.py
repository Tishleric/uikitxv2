#!/usr/bin/env python3
"""
Test expiration data and ListBox population specifically.
"""

import os
from pathlib import Path
from pnl_dashboard import PnLDashboard

def test_expiration_data():
    """Test expiration data loading and display."""
    print("Testing Expiration Data Loading")
    print("=" * 40)
    
    # Show current working directory
    print(f"Current working directory: {os.getcwd()}")
    print(f"CSV files in current dir: {list(Path('.').glob('*.csv'))}")
    
    # Test with explicit path
    current_dir = Path(".").resolve()
    print(f"Absolute path: {current_dir}")
    print(f"CSV files in absolute path: {list(current_dir.glob('*.csv'))}")
    
    # Create dashboard
    print("\n1. Creating dashboard...")
    dashboard = PnLDashboard(".")
    
    print(f"✓ Dashboard data_dir: {dashboard.data_dir}")
    print(f"✓ Available expirations: {dashboard.available_expirations}")
    print(f"✓ All greeks keys: {list(dashboard.all_greeks.keys())}")
    
    # Test expiration options creation
    print("\n2. Testing expiration options...")
    expiration_options = [{"label": exp, "value": exp} for exp in dashboard.available_expirations]
    default_expiration = dashboard.available_expirations[0] if dashboard.available_expirations else None
    
    print(f"✓ Expiration options: {expiration_options}")
    print(f"✓ Default expiration: {default_expiration}")
    
    # Test controls creation
    print("\n3. Testing controls creation...")
    try:
        controls = dashboard.create_controls()
        print("✓ Controls created successfully")
    except Exception as e:
        print(f"✗ Controls creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test layout creation
    print("\n4. Testing layout creation...")
    try:
        layout = dashboard.create_layout()
        print("✓ Layout created successfully")
    except Exception as e:
        print(f"✗ Layout creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_expiration_data()
    if success:
        print("\n🎉 All expiration data tests passed!")
    else:
        print("\n❌ Expiration data tests failed!") 