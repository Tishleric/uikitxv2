#!/usr/bin/env python3
"""Test with correct broker format matching calendar entries."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone, SymbolFormat
import pandas as pd

# Create fresh instance
rs = RosettaStone()

# First, let's see what July broker entries exist
df = pd.read_csv('data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv')
july_entries = df[df['Broker'].str.contains('JUL 25', na=False)][['Option Product', 'Broker', 'Bloomberg_Call']]

print("JULY CALENDAR ENTRIES:")
print("="*70)
for _, row in july_entries.head(10).iterrows():
    print(f"Product: {row['Option Product']}")
    print(f"Broker:  {row['Broker']}")
    print(f"Bloomberg: {row['Bloomberg_Call']}")
    print()

print("\nBROKER TO BLOOMBERG TEST WITH EXACT FORMATS:")
print("="*70)

# Test with exact formats from calendar
test_cases = [
    # Based on actual calendar entries
    ("CALL JUL 25 CBT 10YR TNOTE 111.00", "Monday Weekly (no week info)"),
    ("CALL JUL 25 CBT 10YR TNOTE W4 TUES OPT 111.00", "Tuesday Week 4"),
    ("CALL JUL 25 CBT 10YR TNOTE WED WK4 111.00", "Wednesday Week 4"),
    ("CALL JUL 25 CBT 10YR TNOTE W4 THURS OPT 111.00", "Thursday Week 4"),
]

for symbol, desc in test_cases:
    print(f"\nTest: {desc}")
    print(f"Input: {symbol}")
    
    try:
        result = rs.translate(symbol, "broker", "bloomberg")
        if result:
            print(f"✓ Output: {result}")
        else:
            print(f"✗ Translation failed")
            
            # Debug: parse and check lookup
            parsed = rs.parse_symbol(symbol, SymbolFormat.BROKER)
            lookup_key = f"broker_{parsed.base}_to_bloomberg_{parsed.option_type}"
            print(f"  Looking for: {lookup_key}")
            
            # Find similar
            similar = [k for k in rs.lookups.keys() if "JUL 25" in k and "broker" in k and "bloomberg" in k][:3]
            if similar:
                print("  Similar keys:")
                for s in similar:
                    print(f"    {s} = {rs.lookups[s]}")
                    
    except Exception as e:
        print(f"✗ Error: {e}")

# Show what broker lookups exist for JUL
print("\n\nJULY BROKER LOOKUPS:")
print("="*70)
july_lookups = [(k, v) for k, v in rs.lookups.items() if k.startswith("broker_") and "JUL 25" in k and "bloomberg" in k]
for k, v in sorted(july_lookups)[:10]:
    print(f"{k} = {v}")