"""
Test ZN future selection hardcoded fix.

This test verifies that when multiple futures are present,
the calculator correctly selects the ZN future for all options.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.actant.spot_risk.greek_config import GreekConfiguration, DEFAULT_ENABLED_GREEKS

def test_zn_future_selection():
    """Test that ZN future is selected when multiple futures are present."""
    
    print("=" * 80)
    print("TESTING ZN FUTURE SELECTION")
    print("=" * 80)
    
    # Create test dataframe with multiple futures
    data = [
        # Multiple futures with different prices
        {'key': 'XCME.ZT.SEP25', 'itype': 'F', 'midpoint_price': 110.50, 'strike': None},  # 2-year
        {'key': 'XCME.FV.SEP25', 'itype': 'F', 'midpoint_price': 111.25, 'strike': None},  # 5-year
        {'key': 'XCME.ZN.SEP25', 'itype': 'F', 'midpoint_price': 112.195312, 'strike': None},  # 10-year (target)
        {'key': 'XCME.ZB.SEP25', 'itype': 'F', 'midpoint_price': 125.75, 'strike': None},  # 30-year
        
        # Options (should all use ZN price)
        {'key': 'XCME.ZN.SEP25.110.C', 'itype': 'C', 'midpoint_price': 2.2656250, 'strike': 110.0, 'vtexp': 0.010317},
        {'key': 'XCME.ZN.SEP25.111.P', 'itype': 'P', 'midpoint_price': 0.0546875, 'strike': 111.0, 'vtexp': 0.010317},
    ]
    
    df = pd.DataFrame(data)
    
    # Initialize calculator with all Greeks enabled
    all_greeks = {greek: True for greek in DEFAULT_ENABLED_GREEKS.keys()}
    greek_config = GreekConfiguration(enabled_greeks=all_greeks)
    calculator = SpotRiskGreekCalculator(greek_config=greek_config)
    
    print("\nTest DataFrame:")
    print("-" * 60)
    print(df[['key', 'itype', 'midpoint_price', 'strike']])
    
    try:
        # Run Greek calculations
        df_with_greeks, results = calculator.calculate_greeks(df)
        
        print("\n✅ Greek calculation successful!")
        
        # Check which future price was used
        print("\nOption Greek Results:")
        print("-" * 60)
        for result in results:
            if result.instrument_key and ('C' in result.instrument_key or 'P' in result.instrument_key):
                print(f"\nOption: {result.instrument_key}")
                print(f"  Future price used: {result.future_price}")
                print(f"  Strike: {result.strike}")
                print(f"  Delta_F: {result.delta_F:.4f}" if result.delta_F else "  Delta_F: None")
                
                # Verify ZN price was used
                if result.future_price == 112.195312:
                    print("  ✅ Correctly using ZN future price!")
                else:
                    print(f"  ❌ ERROR: Using wrong future price (expected 112.195312)")
        
    except Exception as e:
        print(f"\n❌ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
        
    # Test 2: No ZN future scenario
    print("\n" + "=" * 80)
    print("TEST 2: Fallback when no ZN future")
    print("=" * 80)
    
    data_no_zn = [
        {'key': 'XCME.ZT.SEP25', 'itype': 'F', 'midpoint_price': 110.50, 'strike': None},
        {'key': 'XCME.FV.SEP25', 'itype': 'F', 'midpoint_price': 111.25, 'strike': None},
        {'key': 'XCME.ZT.SEP25.110.C', 'itype': 'C', 'midpoint_price': 1.5, 'strike': 110.0, 'vtexp': 0.010317},
    ]
    
    df_no_zn = pd.DataFrame(data_no_zn)
    
    try:
        df_with_greeks, results = calculator.calculate_greeks(df_no_zn)
        print("\n✅ Fallback calculation successful!")
        
        for result in results:
            if result.instrument_key and 'C' in result.instrument_key:
                print(f"\nOption: {result.instrument_key}")
                print(f"  Future price used: {result.future_price}")
                print(f"  (Should be first future: 110.50)")
                
    except Exception as e:
        print(f"\n❌ Error during fallback test: {e}")

if __name__ == "__main__":
    test_zn_future_selection()