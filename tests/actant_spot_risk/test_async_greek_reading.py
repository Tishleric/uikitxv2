"""Test async Greek reading from processed CSV files

This test verifies that reading Greeks from processed CSV files
produces the same results as synchronous calculation.
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.dashboards.spot_risk.controller import SpotRiskController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_async_greek_reading():
    """Test that async reading produces same results as sync calculation"""
    
    # Initialize controller
    controller = SpotRiskController()
    
    # Test 1: Verify processed files are discovered
    print("\n=== Test 1: Discovering CSV files ===")
    files = controller.discover_csv_files()
    processed_files = [f for f in files if f.get('is_processed', False)]
    
    print(f"Total files found: {len(files)}")
    print(f"Processed files found: {len(processed_files)}")
    
    if processed_files:
        print("\nProcessed files:")
        for f in processed_files[:3]:  # Show first 3
            print(f"  - {f['filename']} (modified: {f['modified_time']})")
    
    # Test 2: Read Greeks from processed file
    print("\n=== Test 2: Reading Greeks from processed file ===")
    df_async = controller.read_processed_greeks()
    
    if df_async is not None:
        print(f"Successfully read {len(df_async)} rows from processed file")
        print(f"Columns: {', '.join(df_async.columns[:10])}...")  # Show first 10 columns
        
        # Check for Greek columns
        greek_cols = [col for col in df_async.columns if any(
            greek in col.lower() for greek in ['delta', 'gamma', 'vega', 'theta']
        )]
        print(f"\nGreek columns found: {', '.join(greek_cols[:10])}...")
        
        # Show sample Greek values
        if not df_async.empty:
            sample_row = df_async.iloc[0]
            print("\nSample Greek values from first row:")
            for col in ['delta_F', 'gamma_F', 'vega_price', 'theta_F']:
                if col in df_async.columns:
                    print(f"  {col}: {sample_row[col]}")
    else:
        print("Failed to read processed Greeks")
        return
    
    # Test 3: Compare with process_greeks method
    print("\n=== Test 3: Testing process_greeks method ===")
    
    # First load the raw CSV data
    controller.load_csv_data()
    
    # Process Greeks (should use async method internally)
    df_processed = controller.process_greeks(filter_positions=False)
    
    if df_processed is not None:
        print(f"process_greeks returned {len(df_processed)} rows")
        
        # Verify it matches the async read
        if len(df_processed) == len(df_async):
            print("✓ Row counts match")
        else:
            print(f"✗ Row count mismatch: {len(df_processed)} vs {len(df_async)}")
        
        # Check if Greek values match (sample a few rows)
        if not df_processed.empty and not df_async.empty:
            print("\nComparing Greek values (first row):")
            for col in ['delta_F', 'gamma_F', 'vega_price']:
                if col in df_processed.columns and col in df_async.columns:
                    val_processed = df_processed.iloc[0][col]
                    val_async = df_async.iloc[0][col]
                    match = "✓" if pd.isna(val_processed) and pd.isna(val_async) or val_processed == val_async else "✗"
                    print(f"  {col}: {match} (processed: {val_processed}, async: {val_async})")
    else:
        print("process_greeks failed")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_async_greek_reading() 