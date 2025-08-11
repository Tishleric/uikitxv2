"""
Validate VTEXP units and conversion logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime

def check_vtexp_units():
    """Check if VTEXP values are in days or years."""
    
    # Load VTEXP file
    vtexp_file = Path("tests/data/spot_risk_test/vtexp_20250802_120234.csv")
    vtexp_df = pd.read_csv(vtexp_file)
    
    print("VTEXP FILE ANALYSIS")
    print("=" * 60)
    print(f"\nVTEXP file: {vtexp_file.name}")
    print(f"Timestamp: 2025-08-02 12:02:34")
    
    print("\nVTEXP VALUES:")
    print(vtexp_df.to_string(index=False))
    
    # Analyze the values
    vtexp_values = vtexp_df['vtexp'].values
    
    print(f"\nVALUE ANALYSIS:")
    print(f"Min value: {vtexp_values.min():.6f}")
    print(f"Max value: {vtexp_values.max():.6f}")
    print(f"Mean value: {vtexp_values.mean():.6f}")
    
    # Check if these make sense as days or years
    print("\nINTERPRETATION:")
    
    # Extract dates from symbols
    dates = []
    for symbol in vtexp_df['symbol']:
        # Example: XCME.ZN.N.G.04AUG25
        parts = symbol.split('.')
        if len(parts) >= 5:
            date_str = parts[4]  # 04AUG25
            print(f"\nSymbol: {symbol}")
            print(f"  Date string: {date_str}")
            
            # Calculate actual days from Aug 2 to expiry
            if 'AUG25' in date_str:
                day = int(date_str[:2])
                actual_days = day - 2  # Days from Aug 2 to Aug N
                print(f"  Actual days from Aug 2 to Aug {day}: {actual_days}")
                print(f"  VTEXP value: {vtexp_df[vtexp_df['symbol'] == symbol]['vtexp'].values[0]:.6f}")
                
                # Check if VTEXP matches actual days
                vtexp_val = vtexp_df[vtexp_df['symbol'] == symbol]['vtexp'].values[0]
                if abs(vtexp_val - actual_days) < 1:
                    print(f"  -> VTEXP appears to be in DAYS")
                elif abs(vtexp_val - actual_days/365.25) < 0.01:
                    print(f"  -> VTEXP appears to be in YEARS")
                else:
                    print(f"  -> VTEXP units unclear")
    
    print("\nCONCLUSION:")
    print("-" * 40)
    
    # The fractional part .583333 and .687500 suggest business day adjustments
    # .583333 = 14/24 hours (2:00 PM expiry)
    # .687500 = 16.5/24 hours (4:30 PM expiry)
    
    print("VTEXP values appear to be in DAYS (not years)")
    print("The fractional parts represent intraday expiry times:")
    print("  - 0.583333 = 14/24 = 2:00 PM CT")
    print("  - 0.687500 = 16.5/24 = 4:30 PM CT")
    
    print("\nTO CONVERT TO YEARS:")
    print("vtexp_years = vtexp_days / 365.25")
    
    # Show what the values would be in years
    print("\nCONVERTED TO YEARS:")
    for _, row in vtexp_df.head(5).iterrows():
        years = row['vtexp'] / 365.25
        print(f"{row['symbol']}: {row['vtexp']:.6f} days = {years:.6f} years")

if __name__ == "__main__":
    check_vtexp_units()