"""
Test spot risk Greek calculations with VTEXP conversion fix applied.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.actant.spot_risk.greek_config import GreekConfiguration, DEFAULT_ENABLED_GREEKS

def test_greek_calculation_with_fixed_vtexp():
    """Test Greek calculations with corrected VTEXP values."""
    
    print("=" * 80)
    print("TESTING GREEK CALCULATIONS WITH VTEXP FIX")
    print("=" * 80)
    
    # Create test data similar to production
    data = [
        # Future
        {'key': 'XCME.ZN.SEP25', 'itype': 'F', 'midpoint_price': 112.3046875, 'strike': None},
        
        # Options with different expiries
        {'key': 'XCME.HY1.07AUG25.113:25.C', 'itype': 'C', 'midpoint_price': 0.021891, 'strike': 113.25, 
         'vtexp': 2.047917 / 252},  # Apply the /252 fix
        {'key': 'XCME.WY1.06AUG25.112:75.C', 'itype': 'C', 'midpoint_price': 0.030821, 'strike': 112.75,
         'vtexp': 1.047917 / 252},  # Apply the /252 fix
    ]
    
    df = pd.DataFrame(data)
    
    # Initialize calculator
    all_greeks = {greek: True for greek in DEFAULT_ENABLED_GREEKS.keys()}
    greek_config = GreekConfiguration(enabled_greeks=all_greeks)
    calculator = SpotRiskGreekCalculator(greek_config=greek_config)
    
    print("\nTest Data:")
    print("-" * 60)
    print(df[['key', 'itype', 'midpoint_price', 'strike', 'vtexp']])
    
    print("\nVTEXP Values:")
    print("-" * 60)
    for _, row in df.iterrows():
        if row['itype'] in ['C', 'P']:
            vtexp_years = row['vtexp']
            vtexp_days = vtexp_years * 252
            print(f"{row['key']}: {vtexp_years:.6f} years ({vtexp_days:.2f} days)")
    
    try:
        # Calculate Greeks
        df_with_greeks, results = calculator.calculate_greeks(df)
        
        print("\n✅ Greek calculations successful!")
        
        print("\nGreek Results:")
        print("-" * 60)
        print(f"{'Option':<30} {'T (years)':<10} {'Delta':<10} {'Theta':<10} {'IV':<10}")
        print("-" * 60)
        
        for result in results:
            if result.instrument_key and ('C' in result.instrument_key or 'P' in result.instrument_key):
                print(f"{result.instrument_key:<30} {result.time_to_expiry:<10.6f} "
                      f"{result.delta_F:<10.4f} {result.theta_F:<10.4f} "
                      f"{result.implied_volatility:<10.4f}" if result.delta_F else "Failed")
        
        # Compare theta values
        print("\n" + "-" * 60)
        print("THETA ANALYSIS:")
        print("-" * 60)
        
        for result in results:
            if result.theta_F and result.time_to_expiry:
                daily_theta = result.theta_F / 252  # Convert to daily
                print(f"\n{result.instrument_key}:")
                print(f"  Time to expiry: {result.time_to_expiry:.6f} years ({result.time_to_expiry * 252:.1f} days)")
                print(f"  Annual theta: {result.theta_F:.4f}")
                print(f"  Daily theta: {daily_theta:.6f}")
                
                # For very short-dated options, theta should be large (negative)
                if result.time_to_expiry < 0.02:  # Less than ~5 days
                    if abs(daily_theta) > 0.0001:
                        print("  ✅ Reasonable theta for short-dated option")
                    else:
                        print("  ⚠️  Theta seems too small for short-dated option")
        
    except Exception as e:
        print(f"\n❌ Error during calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_greek_calculation_with_fixed_vtexp()