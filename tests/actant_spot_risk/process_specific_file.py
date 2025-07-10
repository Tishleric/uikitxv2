"""Process specific spot risk CSV file with timestamp preservation."""

import sys
from pathlib import Path
# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_full_pipeline import process_spot_risk_csv
import os

if __name__ == "__main__":
    # Specific file requested by user
    input_csv = "data/input/actant_spot_risk/bav_analysis_20250709_193912.csv"
    
    # Create output directory if needed
    os.makedirs("data/output/spot_risk", exist_ok=True)
    
    print(f"Processing specific file: {input_csv}")
    
    # Run the pipeline - will auto-generate output with timestamp
    try:
        result_df = process_spot_risk_csv(input_csv)
        print("\nProcessing completed successfully!")
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc() 