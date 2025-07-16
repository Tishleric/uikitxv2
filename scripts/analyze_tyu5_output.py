import pandas as pd
import os
from glob import glob

# Find the latest TYU5 output file
output_dir = "data/output/pnl"
tyu5_files = glob(os.path.join(output_dir, "tyu5_pnl_all_*.xlsx"))

if not tyu5_files:
    print("No TYU5 output files found")
    exit()

# Get the most recent file
latest_file = max(tyu5_files, key=os.path.getctime)
print(f"Analyzing: {latest_file}")
print("=" * 80)

# Read all sheets
xl_file = pd.ExcelFile(latest_file)
print(f"\nSheets in the Excel file: {xl_file.sheet_names}")
print("=" * 80)

# Analyze each sheet
for sheet_name in xl_file.sheet_names:
    print(f"\n\nSheet: {sheet_name}")
    print("-" * 50)
    
    df = pd.read_excel(latest_file, sheet_name=sheet_name)
    
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    
    if not df.empty:
        print(f"\nFirst 3 rows:")
        print(df.head(3).to_string(index=False, max_cols=10))
        
        # Summary stats for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            print(f"\nNumeric columns summary:")
            for col in numeric_cols[:5]:  # First 5 numeric columns
                if col in df.columns:
                    print(f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")

# Special analysis for key sheets
print("\n\n" + "=" * 80)
print("DETAILED ANALYSIS OF KEY SHEETS")
print("=" * 80)

# Summary sheet
if 'Summary' in xl_file.sheet_names:
    print("\nSummary Sheet Structure:")
    df = pd.read_excel(latest_file, sheet_name='Summary')
    print(df.to_string(index=False))

# Positions sheet
if 'Positions' in xl_file.sheet_names:
    print("\nPositions Sheet Key Info:")
    df = pd.read_excel(latest_file, sheet_name='Positions')
    print(f"  Total positions: {len(df)}")
    print(f"  Columns for UI mapping: {df.columns.tolist()}")
    
# Risk Matrix
if 'Risk_Matrix' in xl_file.sheet_names:
    print("\nRisk Matrix Structure:")
    df = pd.read_excel(latest_file, sheet_name='Risk_Matrix')
    print(f"  Shape: {df.shape}")
    print(f"  Price scenarios: {df.columns[1:].tolist()}") 