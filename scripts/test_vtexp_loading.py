"""Test script to verify vtexp loading from CSV files."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from lib.trading.actant.spot_risk.time_calculator import read_vtexp_from_csv, load_vtexp_for_dataframe
import pandas as pd

logging.basicConfig(level=logging.INFO)

def test_vtexp_loading():
    """Test loading vtexp values from CSV."""
    
    print("Testing vtexp CSV loading...")
    
    # Test 1: Read vtexp from CSV
    try:
        vtexp_map = read_vtexp_from_csv()
        print(f"✓ Successfully loaded {len(vtexp_map)} vtexp values")
        
        # Show sample
        print("\nSample vtexp values:")
        for symbol, vtexp in list(vtexp_map.items())[:5]:
            print(f"  {symbol}: {vtexp}")
    except Exception as e:
        print(f"✗ Failed to load vtexp CSV: {e}")
        return
    
    # Test 2: Create sample dataframe to test mapping
    print("\n\nTesting vtexp mapping to dataframe...")
    
    # Create test data with some matching and non-matching keys
    test_keys = list(vtexp_map.keys())[:3]  # Get first 3 real keys
    test_data = {
        'key': test_keys + ['FAKE.KEY.1', 'FAKE.KEY.2'],
        'itype': ['C', 'P', 'C', 'F', 'C'],
        'strike': [110.0, 112.0, 111.0, 0, 113.0]
    }
    
    df = pd.DataFrame(test_data)
    print("\nTest dataframe:")
    print(df)
    
    # Apply vtexp loading
    from datetime import datetime
    df_with_vtexp = load_vtexp_for_dataframe(df, datetime.now())
    
    print("\nDataframe with vtexp:")
    print(df_with_vtexp)
    
    # Verify results
    print("\nVerification:")
    for idx, row in df_with_vtexp.iterrows():
        if pd.notna(row['vtexp']):
            print(f"  ✓ {row['key']}: vtexp = {row['vtexp']}")
        else:
            if row['itype'] in ['C', 'P']:
                print(f"  ✗ {row['key']}: No vtexp found (option)")
            else:
                print(f"  - {row['key']}: No vtexp expected (future)")

if __name__ == "__main__":
    test_vtexp_loading() 