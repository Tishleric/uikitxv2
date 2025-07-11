"""Check ultima values in processed CSV."""
import pandas as pd
import numpy as np

# Load the CSV
df = pd.read_csv('data/output/spot_risk/bav_analysis_processed_20250709_193912.csv')

# Filter options
options = df[df['itype'].isin(['C', 'P'])]

print(f"Total options: {len(options)}")
print(f"Options with ultima NaN: {pd.isna(options['ultima']).sum()}")
print(f"Options with valid ultima: {pd.notna(options['ultima']).sum()}")
print(f"\nUltima sum: {options['ultima'].sum()}")
print(f"Volga sum: {options['volga_price'].sum()}")
print(f"Zomma sum: {options['zomma'].sum()}")

# Check aggregate rows
agg_rows = df[df['key'].str.startswith('AGGREGATE_', na=False)]
print("\nAggregate rows:")
for _, row in agg_rows.iterrows():
    print(f"{row['key']}: ultima={row['ultima']}, volga={row['volga_price']}, zomma={row['zomma']}") 