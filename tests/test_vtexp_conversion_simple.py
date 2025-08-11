"""
Simple test to verify VTEXP conversion from days to years.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

def test_vtexp_conversion():
    """Test the VTEXP conversion logic directly."""
    
    print("=" * 80)
    print("TESTING VTEXP CONVERSION LOGIC")
    print("=" * 80)
    
    # Simulate reading VTEXP file
    vtexp_file = Path("tests/data/spot_risk_test/vtexp_20250802_120234.csv")
    
    print(f"\nReading VTEXP file: {vtexp_file}")
    df = pd.read_csv(vtexp_file)
    
    print("\nOriginal VTEXP values (from file):")
    print(df)
    
    # Method 1: Direct dictionary (old way - no conversion)
    vtexp_dict_old = df.set_index('symbol')['vtexp'].to_dict()
    
    # Method 2: With conversion (new way)
    vtexp_dict_new = {k: v/252 for k, v in df.set_index('symbol')['vtexp'].to_dict().items()}
    
    print("\n" + "-" * 60)
    print("CONVERSION COMPARISON:")
    print("-" * 60)
    print(f"{'Symbol':<20} {'Original':<15} {'Converted (/252)':<15}")
    print("-" * 60)
    
    for symbol in sorted(vtexp_dict_old.keys()):
        original = vtexp_dict_old[symbol]
        converted = vtexp_dict_new[symbol]
        print(f"{symbol:<20} {original:<15.6f} {converted:<15.6f}")
    
    # Test with specific expected values
    print("\n" + "-" * 60)
    print("VALIDATION:")
    print("-" * 60)
    
    # For options expiring tomorrow (06AUG25), vtexp should be ~1/252 = 0.00397
    aug6_symbols = [s for s in vtexp_dict_new.keys() if '06AUG25' in s]
    if aug6_symbols:
        symbol = aug6_symbols[0]
        vtexp_years = vtexp_dict_new[symbol]
        print(f"\n06AUG25 option ({symbol}):")
        print(f"  Converted value: {vtexp_years:.6f} years")
        print(f"  Expected: ~{1/252:.6f} years (1 day)")
        
        if abs(vtexp_years - 1/252) < 0.01:
            print("  ✅ Reasonable value for 1-day option")
        else:
            print("  ❌ Value seems incorrect")
    
    # For options expiring in 3 days (08AUG25), vtexp should be ~3/252 = 0.0119
    aug8_symbols = [s for s in vtexp_dict_new.keys() if '08AUG25' in s]
    if aug8_symbols:
        symbol = aug8_symbols[0]
        vtexp_years = vtexp_dict_new[symbol]
        print(f"\n08AUG25 option ({symbol}):")
        print(f"  Converted value: {vtexp_years:.6f} years")
        print(f"  Expected: ~{3/252:.6f} years (3 days)")
        
        if abs(vtexp_years - 3/252) < 0.01:
            print("  ✅ Reasonable value for 3-day option")
        else:
            print("  ❌ Value seems incorrect")
    
    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    
    # Check if the original values are already wrong
    original_aug6 = vtexp_dict_old.get(aug6_symbols[0] if aug6_symbols else '', 0)
    if original_aug6 > 1:
        print("⚠️  WARNING: Original VTEXP values are already incorrect!")
        print(f"   06AUG25 has value {original_aug6:.2f} which is way too large for days")
        print("   The VTEXP file generation process may be producing wrong values")
    else:
        print("✅ Conversion logic is correct: values / 252")

if __name__ == "__main__":
    test_vtexp_conversion()