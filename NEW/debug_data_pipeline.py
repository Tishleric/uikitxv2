#!/usr/bin/env python3
"""
Debug script to trace data pipeline from CSV to dashboard.
"""

import sys
from pathlib import Path
import pandas as pd

# Add lib path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

def debug_csv_loading():
    """Debug CSV loading step by step."""
    print("=== DEBUG: CSV Loading Pipeline ===")
    
    # Step 1: Direct CSV read
    print("\n1. Direct CSV Read:")
    df = pd.read_csv("GE_XCME.ZN_20250610_103938.csv")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)[:5]}...")
    
    # Step 2: Test parser import
    print("\n2. Testing Parser Import:")
    try:
        from csv_parser import ActantCSVParser, load_latest_data
        print("   ✓ Parser imports successful")
    except Exception as e:
        print(f"   ✗ Parser import failed: {e}")
        return
    
    # Step 3: Test parser initialization
    print("\n3. Testing Parser Initialization:")
    parser = ActantCSVParser()
    print(f"   ✓ Parser created with shock_multiplier: {parser.shock_multiplier}")
    
    # Step 4: Test file parsing
    print("\n4. Testing File Parsing:")
    try:
        parsed_df = parser.parse_file(Path("GE_XCME.ZN_20250610_103938.csv"))
        print(f"   ✓ File parsed successfully: {parsed_df.shape}")
    except Exception as e:
        print(f"   ✗ File parsing failed: {e}")
        return
    
    # Step 5: Test expiration extraction
    print("\n5. Testing Expiration Extraction:")
    expirations = parser.get_expirations(parsed_df)
    print(f"   ✓ Found expirations: {expirations}")
    
    # Step 6: Test greeks extraction
    print("\n6. Testing Greeks Extraction:")
    try:
        from pnl_calculations import parse_actant_csv_to_greeks
        
        for exp in expirations:
            greeks = parse_actant_csv_to_greeks(parsed_df, exp)
            print(f"   ✓ {exp}: ATM call price = {greeks.call_prices[greeks.atm_index]:.2f}")
            print(f"     Shock range: {greeks.shocks.min():.1f} to {greeks.shocks.max():.1f} bp")
            
    except Exception as e:
        print(f"   ✗ Greeks extraction failed: {e}")
        return
    
    # Step 7: Test load_latest_data function
    print("\n7. Testing load_latest_data:")
    try:
        df_latest, all_greeks = load_latest_data(Path("."))
        print(f"   ✓ Loaded data for {len(all_greeks)} expirations")
        for exp, greeks in all_greeks.items():
            print(f"     {exp}: {len(greeks.shocks)} shocks")
    except Exception as e:
        print(f"   ✗ load_latest_data failed: {e}")
        return
    
    print("\n=== Pipeline Debug Complete ===")
    return all_greeks

def debug_dashboard_data():
    """Debug how data flows into dashboard."""
    print("\n=== DEBUG: Dashboard Data Flow ===")
    
    try:
        from pnl_dashboard import PnLDashboard
        
        # Test dashboard initialization
        print("\n1. Testing Dashboard Initialization:")
        dashboard = PnLDashboard(".")
        print(f"   ✓ Dashboard created")
        print(f"   Available expirations: {list(dashboard.available_expirations.keys())}")
        
        # Test data access
        print("\n2. Testing Data Access:")
        for exp, greeks in dashboard.available_expirations.items():
            print(f"   {exp}:")
            print(f"     Shocks: {len(greeks.shocks)} points")
            print(f"     ATM call price: {greeks.call_prices[greeks.atm_index]:.2f}")
            print(f"     ATM put price: {greeks.put_prices[greeks.atm_index]:.2f}")
        
    except Exception as e:
        print(f"   ✗ Dashboard initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    all_greeks = debug_csv_loading()
    if all_greeks:
        debug_dashboard_data() 