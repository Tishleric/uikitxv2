#!/usr/bin/env python
"""
Simple script to process Spot Risk CSV files with Greek calculations.

Usage:
    python process_spot_risk.py <input_csv_file>
    
Example:
    python process_spot_risk.py data/input/actant_spot_risk/bav_analysis_20250709_193912.csv

The script will:
1. Parse the CSV file using adjtheor as primary price source
2. Calculate Greeks using the bond future options API
3. Save output with timestamp preserved (e.g., bav_analysis_processed_20250709_193912.csv)
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.actant_spot_risk.test_full_pipeline import process_spot_risk_csv

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs("data/output/spot_risk", exist_ok=True)
    
    print(f"Processing: {input_file}")
    
    try:
        # Process the file
        result_df = process_spot_risk_csv(input_file)
        print("\nProcessing completed successfully!")
        print("Check data/output/spot_risk/ for the processed file.")
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 