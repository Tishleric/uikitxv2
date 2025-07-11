"""Quick test script to verify aggregate row display with Greek space filtering."""

import pandas as pd
from pathlib import Path

def test_aggregate_display():
    """Test that aggregate rows are properly filtered by Greek space."""
    
    # Find a processed CSV file with aggregate rows
    output_dir = Path("data/output/spot_risk")
    csv_files = list(output_dir.glob("bav_analysis_processed_*.csv"))
    
    if not csv_files:
        print("No processed CSV files found")
        return
        
    # Use the most recent file
    csv_file = sorted(csv_files)[-1]
    print(f"Testing with: {csv_file.name}")
    
    # Load the CSV
    df = pd.read_csv(csv_file)
    
    # Check for aggregate rows
    aggregate_rows = df[df['key'].str.startswith('AGGREGATE_', na=False)]
    
    if aggregate_rows.empty:
        print("No aggregate rows found in the file")
        return
        
    print(f"\nFound {len(aggregate_rows)} aggregate rows:")
    for _, row in aggregate_rows.iterrows():
        key = row['key']
        position = row.get('pos.position', 0)
        
        # Check which Greek columns have values
        greek_cols = []
        for col in ['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 'vega_price', 
                   'theta_F', 'volga_price', 'ultima', 'zomma']:
            if col in df.columns:
                try:
                    value = float(row[col])
                    if value != 0:
                        greek_cols.append(f"{col}={value:.4f}")
                except (ValueError, TypeError):
                    pass
        
        print(f"  {key}: position={position}, Greeks: {', '.join(greek_cols[:3])}...")
    
    # Test Greek space filtering logic
    print("\nTesting Greek space filtering:")
    
    # Simulate F-space filter
    greek_space = 'F'
    f_space_rows = []
    for _, row in aggregate_rows.iterrows():
        key = row['key']
        if f'_{greek_space}' in key:  # Old logic (case sensitive)
            f_space_rows.append(key)
    print(f"  F-space (old logic): {f_space_rows}")
    
    # New logic with uppercase
    f_space_rows_new = []
    for _, row in aggregate_rows.iterrows():
        key = row['key']
        if f'_{greek_space.upper()}' in key:  # New logic (uppercase)
            f_space_rows_new.append(key)
    print(f"  F-space (new logic): {f_space_rows_new}")
    
    # Simulate Y-space filter
    greek_space = 'y'
    y_space_rows = []
    for _, row in aggregate_rows.iterrows():
        key = row['key']
        if f'_{greek_space}' in key:  # Old logic (case sensitive)
            y_space_rows.append(key)
    print(f"  Y-space (old logic): {y_space_rows}")
    
    # New logic with uppercase
    y_space_rows_new = []
    for _, row in aggregate_rows.iterrows():
        key = row['key']
        if f'_{greek_space.upper()}' in key:  # New logic (uppercase)
            y_space_rows_new.append(key)
    print(f"  Y-space (new logic): {y_space_rows_new}")

if __name__ == "__main__":
    test_aggregate_display() 