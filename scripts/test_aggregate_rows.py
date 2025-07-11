"""Script to test aggregate rows functionality in spot risk processing."""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.actant.spot_risk import parse_spot_risk_csv, SpotRiskGreekCalculator


def main():
    """Test aggregate rows calculation on a sample CSV file."""
    
    # Find a sample CSV file
    input_dir = Path("data/input/actant_spot_risk")
    csv_files = list(input_dir.glob("bav_analysis_*.csv"))
    
    if not csv_files:
        print("No CSV files found in input directory")
        return
    
    # Use the first file
    csv_file = csv_files[0]
    print(f"Processing: {csv_file.name}")
    
    # Parse the CSV
    df = parse_spot_risk_csv(csv_file)
    print(f"Parsed {len(df)} rows")
    
    # Initialize calculator and calculate Greeks
    calculator = SpotRiskGreekCalculator()
    df_with_greeks, results = calculator.calculate_greeks(df)
    print(f"Calculated Greeks for {len(results)} options")
    
    # Calculate aggregates
    df_with_aggregates = calculator.calculate_aggregates(df_with_greeks)
    print(f"Total rows after aggregates: {len(df_with_aggregates)}")
    
    # Extract and display aggregate rows
    aggregate_rows = df_with_aggregates[df_with_aggregates['key'].str.startswith('AGGREGATE_')]
    print(f"\nFound {len(aggregate_rows)} aggregate rows:")
    
    # Display aggregate data
    for _, row in aggregate_rows.iterrows():
        print(f"\n{row['key']}:")
        print(f"  Position: {row['pos.position']}")
        print(f"  Delta_F: {row.get('delta_F', 'N/A')}")
        print(f"  Delta_y: {row.get('delta_y', 'N/A')}")
        print(f"  Gamma_F: {row.get('gamma_F', 'N/A')}")
        print(f"  Gamma_y: {row.get('gamma_y', 'N/A')}")
        print(f"  Vega_price: {row.get('vega_price', 'N/A')}")
        print(f"  Theta_F: {row.get('theta_F', 'N/A')}")
    
    # Save output for inspection
    output_file = Path("data/output/spot_risk/test_aggregates.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_with_aggregates.to_csv(output_file, index=False)
    print(f"\nSaved output to: {output_file}")
    
    # Test filtering logic
    print("\n\nTesting F-space filtering:")
    f_space_rows = []
    for _, row in df_with_aggregates.iterrows():
        key = row.get('key', '')
        if key.startswith('AGGREGATE_') and '_F' in key:
            f_space_rows.append(row['key'])
        elif not key.startswith('AGGREGATE_'):
            # Include regular rows
            pass
    print(f"F-space aggregate rows: {f_space_rows}")
    
    print("\nTesting Y-space filtering:")
    y_space_rows = []
    for _, row in df_with_aggregates.iterrows():
        key = row.get('key', '')
        if key.startswith('AGGREGATE_') and '_Y' in key:
            y_space_rows.append(row['key'])
        elif not key.startswith('AGGREGATE_'):
            # Include regular rows
            pass
    print(f"Y-space aggregate rows: {y_space_rows}")


if __name__ == "__main__":
    main() 