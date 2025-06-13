"""
Test JSON parsing with the provided sample file
"""

import json
import os
from actant_parser import parse_json

# Test with the sample JSON file
test_file = "GE_XCME.ZN_20250612_214323.json"

if os.path.exists(test_file):
    print(f"Testing JSON parsing with: {test_file}")
    print("-" * 50)
    
    # Load and examine structure
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    print("JSON Structure:")
    print(f"- Top level keys: {list(data.keys())}")
    
    if 'totals' in data:
        print(f"- Number of totals: {len(data['totals'])}")
        for i, total in enumerate(data['totals'][:3]):  # Show first 3
            print(f"  - Total {i}: {total.get('header', 'Unknown')}")
            if 'points' in total:
                print(f"    - Number of points: {len(total['points'])}")
                # Show shock values
                shocks = [p.get('header') for p in total['points'][:5]]
                print(f"    - First 5 shock values: {shocks}")
    
    print("\n" + "-" * 50)
    print("Parsing Results:")
    
    # Parse using our function
    df = parse_json(test_file)
    
    if not df.empty:
        print(f"\nSuccessfully parsed {len(df)} records:")
        print(df.to_string())
        
        print("\nSample ATM option data:")
        for _, row in df.iterrows():
            print(f"\nScenario: {row['scenario']}")
            print(f"  Future Price (F): {row['F']:.5f}")
            print(f"  Strike (K): {row['K']:.5f}")
            print(f"  Time to Expiry: {row['T']:.4f} years ({row['T'] * 365:.1f} days)")
            print(f"  Volatility: {row['Vol']:.2f}%")
    else:
        print("ERROR: No data extracted from JSON!")
else:
    print(f"ERROR: Test file '{test_file}' not found!")
    print("Available files:")
    for f in os.listdir('.'):
        if f.endswith('.json'):
            print(f"  - {f}") 