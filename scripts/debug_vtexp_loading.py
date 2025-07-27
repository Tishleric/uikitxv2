#!/usr/bin/env python3
"""Debug vtexp loading in spot risk pipeline."""

import sys
sys.path.append('.')

from pathlib import Path
import pandas as pd
from lib.trading.actant.spot_risk.time_calculator import read_vtexp_from_csv, load_vtexp_for_dataframe
from lib.trading.actant.spot_risk.parser import extract_datetime_from_filename
from datetime import datetime

def debug_vtexp():
    """Debug vtexp loading issues."""
    
    print("=== DEBUGGING VTEXP LOADING ===\n")
    
    # Step 1: Check vtexp CSV
    print("1. Loading vtexp CSV:")
    vtexp_map = read_vtexp_from_csv()
    print(f"  Loaded {len(vtexp_map)} vtexp entries")
    
    # Show sample entries
    print("\n  Sample vtexp entries:")
    for symbol, vtexp in list(vtexp_map.items())[:5]:
        print(f"    {symbol}: {vtexp:.6f}")
    
    # Step 2: Load a spot risk file
    print("\n2. Loading spot risk file:")
    spot_risk_file = Path("data/input/actant_spot_risk/2025-07-24/bav_analysis_20250723_170920.csv")
    
    if not spot_risk_file.exists():
        print(f"  ❌ File not found: {spot_risk_file}")
        return
    
    df = pd.read_csv(spot_risk_file)
    df = df.iloc[1:].reset_index(drop=True)  # Skip type row
    print(f"  Loaded {len(df)} rows")
    
    # Show sample spot risk symbols
    print("\n  Sample spot risk symbols (key column):")
    for key in df['key'].head(5):
        print(f"    {key}")
    
    # Step 3: Test vtexp mapping
    print("\n3. Testing vtexp mapping:")
    csv_timestamp = extract_datetime_from_filename(spot_risk_file)
    print(f"  CSV timestamp: {csv_timestamp}")
    
    # Create a small test DataFrame
    test_df = df.head(10).copy()
    
    # Apply vtexp loading
    result_df = load_vtexp_for_dataframe(test_df, csv_timestamp)
    
    # Check results
    print("\n  Mapping results:")
    for idx, row in result_df.iterrows():
        key = row.get('key', 'N/A')
        vtexp = row.get('vtexp', None)
        if pd.notna(vtexp):
            print(f"    ✅ {key}: vtexp = {vtexp:.6f}")
        else:
            print(f"    ❌ {key}: vtexp = None")
    
    # Step 4: Diagnose mapping issues
    print("\n4. Diagnosing mapping issues:")
    
    # Check what format vtexp_mapper expects
    from lib.trading.actant.spot_risk.vtexp_mapper import VtexpSymbolMapper
    mapper = VtexpSymbolMapper()
    
    # Try direct mapping
    test_symbol = "XCME.VY3.21JUL25.111.C"
    print(f"\n  Testing direct mapping for: {test_symbol}")
    
    # Extract expiry from spot risk symbol
    spot_risk_expiry = mapper.extract_expiry_from_spot_risk(test_symbol)
    print(f"    Extracted expiry from spot risk: {spot_risk_expiry}")
    
    # Find matching vtexp entry
    vtexp_key = None
    for vtexp_symbol in vtexp_map:
        vtexp_expiry = mapper.extract_expiry_from_vtexp(vtexp_symbol)
        if vtexp_expiry == spot_risk_expiry:
            vtexp_key = vtexp_symbol
            break
    
    print(f"    Matching vtexp key: {vtexp_key}")
    
    if vtexp_key in vtexp_map:
        print(f"    ✅ Found in vtexp map: {vtexp_map[vtexp_key]:.6f}")
    else:
        print(f"    ❌ Not found in vtexp map")
        
        # Show similar keys
        print("\n    Similar keys in vtexp map:")
        for key in vtexp_map:
            if "21JUL25" in key:
                print(f"      {key}")

if __name__ == "__main__":
    debug_vtexp() 