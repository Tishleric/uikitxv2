#!/usr/bin/env python3
"""Test vtexp mapping with ActantTime format."""

import sys
sys.path.append('.')

from pathlib import Path
import pandas as pd
from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_vtexp_mapping():
    """Test that spot risk symbols can be mapped to vtexp via ActantTime."""
    
    print("=== TESTING VTEXP MAPPING WITH ACTANTTIME ===\n")
    
    # Load a vtexp CSV
    vtexp_dir = Path("data/input/vtexp")
    vtexp_files = list(vtexp_dir.glob("vtexp_*.csv"))
    
    if not vtexp_files:
        print("❌ No vtexp files found!")
        return False
    
    # Use most recent
    vtexp_file = max(vtexp_files, key=lambda p: p.stat().st_mtime)
    print(f"Using vtexp file: {vtexp_file}")
    
    vtexp_df = pd.read_csv(vtexp_file)
    print(f"Loaded {len(vtexp_df)} vtexp entries")
    
    # Show sample vtexp entries
    print("\nSample vtexp entries:")
    for _, row in vtexp_df.head(5).iterrows():
        print(f"  {row['symbol']}: {row['vtexp']:.6f}")
    
    # Test RosettaStone translation from ActantRisk to ActantTime
    print("\n\nTesting ActantRisk → ActantTime translation:")
    rosetta = RosettaStone()
    
    test_symbols = [
        "XCME.VY3.21JUL25.111.C",
        "XCME.ZN1.01AUG25.111.C", 
        "XCME.OZN.AUG25.111.C",
        "XCME.HY4.24JUL25.111.P"
    ]
    
    for symbol in test_symbols:
        actant_time = rosetta.translate(symbol, 'actantrisk', 'actanttime')
        print(f"\n{symbol}")
        print(f"  → ActantTime: {actant_time}")
        
        # Check if this ActantTime exists in vtexp
        if actant_time:
            # Remove strike and option type for vtexp lookup
            vtexp_key = actant_time.rsplit('.', 2)[0] if '.' in actant_time else actant_time
            match = vtexp_df[vtexp_df['symbol'] == vtexp_key]
            if not match.empty:
                print(f"  ✅ Found in vtexp: {match.iloc[0]['vtexp']:.6f}")
            else:
                print(f"  ❌ Not found in vtexp (looking for: {vtexp_key})")
        else:
            print(f"  ❌ Translation failed")
    
    # Test the calendar mapping
    print("\n\nChecking calendar ActantTime format:")
    calendar_df = pd.read_csv("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
    
    # Check ActantTime column format
    actant_time_samples = calendar_df['ActantTime'].dropna().head(10)
    print("\nSample ActantTime entries from calendar:")
    for val in actant_time_samples:
        print(f"  {val}")
    
    # Verify all use ZN.N.G pattern
    pattern_check = calendar_df['ActantTime'].str.contains(r'ZN\.[A-Z]\.G', na=False)
    unique_patterns = calendar_df.loc[pattern_check, 'ActantTime'].str.extract(r'(ZN\.[A-Z]\.G)')[0].unique()
    
    print(f"\nUnique patterns found: {unique_patterns}")
    
    if len(unique_patterns) == 1 and unique_patterns[0] == 'ZN.N.G':
        print("✅ All ActantTime entries use correct ZN.N.G pattern")
    else:
        print("❌ ActantTime entries have inconsistent patterns")
    
    return True

if __name__ == "__main__":
    try:
        test_vtexp_mapping()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 