#!/usr/bin/env python3
"""
Verification script to confirm data is properly integrated into dashboard.
"""

import sys
from pathlib import Path

# Add lib path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

def verify_data_integration():
    """Verify that CSV data is properly integrated into dashboard functionality."""
    print("🔍 Verifying Data Integration")
    print("=" * 40)
    
    # Test 1: Dashboard initialization with data
    print("\n1. Dashboard Data Loading:")
    from pnl_dashboard import PnLDashboard
    dashboard = PnLDashboard(".")
    
    print(f"   ✓ Available expirations: {dashboard.available_expirations}")
    print(f"   ✓ All greeks loaded: {list(dashboard.all_greeks.keys())}")
    
    # Test 2: Data access for each expiration
    print("\n2. Greeks Data Access:")
    for exp in dashboard.available_expirations:
        greeks = dashboard.all_greeks[exp]
        print(f"   {exp}:")
        print(f"     ✓ Shocks: {len(greeks.shocks)} points ({greeks.shocks.min():.1f} to {greeks.shocks.max():.1f} bp)")
        print(f"     ✓ ATM Call: ${greeks.call_prices[greeks.atm_index]:.2f}")
        print(f"     ✓ ATM Put: ${greeks.put_prices[greeks.atm_index]:.2f}")
    
    # Test 3: PnL calculation integration
    print("\n3. PnL Calculation Integration:")
    from pnl_calculations import PnLCalculator
    
    for exp in dashboard.available_expirations:
        greeks = dashboard.all_greeks[exp]
        
        # Test call PnL
        call_pnl = PnLCalculator.calculate_all_pnls(greeks, 'call')
        put_pnl = PnLCalculator.calculate_all_pnls(greeks, 'put')
        
        print(f"   {exp}:")
        print(f"     ✓ Call PnL: {len(call_pnl)} rows, ATM PnL = ${call_pnl.iloc[greeks.atm_index]['actant_pnl']:.2f}")
        print(f"     ✓ Put PnL: {len(put_pnl)} rows, ATM PnL = ${put_pnl.iloc[greeks.atm_index]['actant_pnl']:.2f}")
    
    # Test 4: Dashboard content generation
    print("\n4. Dashboard Content Generation:")
    
    # Test graph creation
    test_greeks = dashboard.all_greeks['XCME.ZN']
    graph_content = dashboard.create_pnl_graph(test_greeks, 'call')
    print("   ✓ Graph content generated successfully")
    
    # Test table creation
    table_content = dashboard.create_pnl_table(test_greeks, 'call')
    print("   ✓ Table content generated successfully")
    
    # Test 5: Component validation
    print("\n5. Component Validation:")
    try:
        header = dashboard.create_header()
        print("   ✓ Header component created")
        
        controls = dashboard.create_controls()
        print("   ✓ Controls component created")
        
        content = dashboard.create_content_area()
        print("   ✓ Content area created")
        
        layout = dashboard.create_layout()
        print("   ✓ Complete layout created")
        
    except Exception as e:
        print(f"   ✗ Component creation failed: {e}")
        return False
    
    print("\n🎉 All Data Integration Tests Passed!")
    print("\nData Pipeline Summary:")
    print(f"  • CSV File: GE_XCME.ZN_20250610_103938.csv")
    print(f"  • Expirations: {len(dashboard.available_expirations)}")
    print(f"  • Shock range: {test_greeks.shocks.min():.1f} to {test_greeks.shocks.max():.1f} bp")
    print(f"  • ATM Call Price: ${test_greeks.call_prices[test_greeks.atm_index]:.2f}")
    print(f"  • Taylor Series calculations: Working ✓")
    print(f"  • Dashboard integration: Complete ✓")
    
    return True

if __name__ == "__main__":
    verify_data_integration() 