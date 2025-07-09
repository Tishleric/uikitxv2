"""Test full spot risk processing pipeline with actual CSV data."""

import sys
from pathlib import Path
# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def process_spot_risk_csv(input_file: str, output_file: str):
    """Process spot risk CSV through full pipeline."""
    
    print(f"\n{'='*60}")
    print(f"SPOT RISK PROCESSING PIPELINE")
    print(f"{'='*60}\n")
    
    # Step 1: Parse CSV
    print("Step 1: Parsing CSV file...")
    df = parse_spot_risk_csv(input_file, calculate_time_to_expiry=True)
    print(f"✓ Parsed {len(df)} rows from CSV")
    print(f"  Columns: {', '.join(df.columns[:10])}...")
    
    # Show data types
    print("\nInstrument types found:")
    print(df['itype'].value_counts())
    
    # Step 2: Verify time to expiry was calculated
    print("\nStep 2: Verifying time to expiry calculation...")
    if 'vtexp' in df.columns:
        vtexp_stats = df['vtexp'].describe()
        print(f"✓ vtexp column present - mean: {vtexp_stats['mean']:.4f} years")
        print(f"  Options with vtexp: {df['vtexp'].notna().sum()}")
    else:
        print("❌ Warning: vtexp column not found!")
    
    # Step 3: Calculate Greeks
    print("\nStep 3: Calculating Greeks...")
    greek_calc = SpotRiskGreekCalculator()
    
    try:
        df_with_greeks, greek_results = greek_calc.calculate_greeks(df)
        print(f"✓ Calculated Greeks for {len(greek_results)} options")
        
        # Show some results
        success_count = sum(1 for r in greek_results if r.success)
        print(f"  Successful: {success_count}")
        print(f"  Failed: {len(greek_results) - success_count}")
        
        # Sample some successful calculations
        print("\nSample Greek calculations:")
        for i, result in enumerate(greek_results[:5]):
            if result.success:
                print(f"  {result.instrument_key}: IV={result.implied_volatility:.4f}, "
                      f"Delta={result.delta_F:.4f}, Gamma={result.gamma_F:.6f}")
        
    except Exception as e:
        print(f"❌ Error during Greek calculation: {e}")
        raise
    
    # Step 4: Sort and prepare output
    print("\nStep 4: Preparing output...")
    
    # Sort by instrument key
    df_sorted = df_with_greeks.sort_values('key')
    
    # Show summary statistics
    print("\nGreek calculation summary:")
    print(f"  Total rows: {len(df_sorted)}")
    print(f"  Futures: {len(df_sorted[df_sorted['itype'] == 'F'])}")
    print(f"  Options with Greeks: {df_sorted['greek_calc_success'].sum()}")
    
    # Show columns added
    greek_columns = ['calc_vol', 'delta_F', 'delta_y', 'gamma_F', 'gamma_y', 
                     'vega_price', 'theta_F', 'volga_price']
    print("\nGreek columns added:")
    for col in greek_columns[:5]:
        if col in df_sorted.columns:
            non_nan = df_sorted[col].notna().sum()
            print(f"  {col}: {non_nan} non-NaN values")
    
    # Step 5: Save to output
    print(f"\nStep 5: Saving to {output_file}...")
    df_sorted.to_csv(output_file, index=False)
    print(f"✓ Saved {len(df_sorted)} rows to output file")
    
    # Show first few rows of output
    print("\nFirst 5 rows of output:")
    print(df_sorted[['key', 'itype', 'strike', 'midpoint_price', 
                     'calc_vol', 'delta_F', 'gamma_F']].head())
    
    return df_sorted


if __name__ == "__main__":
    # Input and output files
    input_csv = "data/input/actant_spot_risk/bav_analysis_20250708_104022.csv"
    output_csv = "data/output/spot_risk/bav_analysis_processed.csv"
    
    # Create output directory if needed
    import os
    os.makedirs("data/output/spot_risk", exist_ok=True)
    
    # Run the pipeline
    result_df = process_spot_risk_csv(input_csv, output_csv)
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE!")
    print(f"Output saved to: {output_csv}")
    print(f"{'='*60}") 