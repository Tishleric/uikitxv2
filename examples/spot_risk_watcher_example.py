"""Example usage of the Spot Risk file watcher with daily subfolder support.

This example demonstrates:
1. Starting the file watcher
2. Processing files in date subfolders
3. Handling files placed in root directory
"""

import os
import time
import logging
from pathlib import Path

from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the Spot Risk file watcher example."""
    # Define input and output directories
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "data" / "input" / "actant_spot_risk"
    output_dir = project_root / "data" / "output" / "spot_risk"
    
    print(f"Starting Spot Risk File Watcher")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    # Create the watcher
    watcher = SpotRiskWatcher(str(input_dir), str(output_dir))
    
    try:
        # Start watching
        watcher.start()
        print("Watcher started successfully!")
        print("\nFile structure support:")
        print("- Files in /actant_spot_risk/YYYY-MM-DD/ → /spot_risk/YYYY-MM-DD/")
        print("- Files in /actant_spot_risk/ → /spot_risk/YYYY-MM-DD/ (auto-dated)")
        print("- Date boundaries: 3pm EST to 3pm EST")
        print("\nPress Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        watcher.stop()
        print("Watcher stopped.")
    except Exception as e:
        print(f"Error: {e}")
        watcher.stop()
        raise


if __name__ == "__main__":
    main() 