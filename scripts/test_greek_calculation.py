#!/usr/bin/env python
"""Test Greek calculation with vtexp mapping."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator

# Parse a spot risk CSV with vtexp calculation
csv_file = Path("data/input/actant_spot_risk/2025-07-12/bav_analysis_20250711_191400.csv")
if not csv_file.exists():
    print(f"File not found: {csv_file}")
    sys.exit(1)

print(f"Parsing {csv_file.name}...")
df = parse_spot_risk_csv(csv_file, calculate_time_to_expiry=True)

# Check vtexp values
print(f"\nTotal rows: {len(df)}")
print(f"Options with vtexp: {df[df['itype'].isin(['C', 'P']) & df['vtexp'].notna()].shape[0]}")
print(f"Options without vtexp: {df[df['itype'].isin(['C', 'P']) & df['vtexp'].isna()].shape[0]}")

# Show sample of options with vtexp
with_vtexp = df[df['itype'].isin(['C', 'P']) & df['vtexp'].notna()]
if len(with_vtexp) > 0:
    print("\nSample options WITH vtexp:")
    print(with_vtexp[['key', 'vtexp']].head())

# Show sample of options without vtexp
without_vtexp = df[df['itype'].isin(['C', 'P']) & df['vtexp'].isna()]
if len(without_vtexp) > 0:
    print("\nSample options WITHOUT vtexp:")
    print(without_vtexp[['key']].head())

# Try calculating Greeks
print("\n=== Testing Greek Calculation ===")
calculator = SpotRiskGreekCalculator()

# Get a small sample for testing
sample_df = df.head(20).copy()
print(f"Calculating Greeks for {len(sample_df)} rows...")

try:
    df_with_greeks, results = calculator.calculate_greeks(sample_df)
    
    # Summary
    success_count = sum(1 for r in results if r.success)
    print(f"\nGreek calculations: {success_count} successful, {len(results) - success_count} failed")
    
    # Show failures
    failures = [r for r in results if not r.success]
    if failures:
        print("\nSample failures:")
        for failure in failures[:5]:
            print(f"  {failure.instrument_key}: {failure.error}")
            
except Exception as e:
    print(f"Error calculating Greeks: {e}")
    import traceback
    traceback.print_exc() 