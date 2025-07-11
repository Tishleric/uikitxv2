#!/usr/bin/env python
"""Run the Spot Risk file watcher service.

This script monitors the input directory for new Spot Risk CSV files
and automatically processes them with Greek calculations.

Usage:
    python run_spot_risk_watcher.py
    
Press Ctrl+C to stop the watcher.
"""

import sys
import signal
import logging
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Directories
INPUT_DIR = "data/input/actant_spot_risk"
OUTPUT_DIR = "data/output/spot_risk"


def main():
    """Main entry point for the watcher service."""
    print("="*60)
    print("Spot Risk File Watcher Service")
    print("="*60)
    print(f"\nMonitoring: {INPUT_DIR}")
    print(f"Output to: {OUTPUT_DIR}")
    print("\nPress Ctrl+C to stop\n")
    
    # Create watcher
    watcher = SpotRiskWatcher(INPUT_DIR, OUTPUT_DIR)
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n\nShutting down watcher...")
        watcher.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start watching
        watcher.start()
        
        # Keep the main thread alive
        print("Watcher is running...")
        
        # Use a simple loop instead of signal.pause() for Windows compatibility
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nShutting down watcher...")
        watcher.stop()
    except Exception as e:
        print(f"\nError: {e}")
        watcher.stop()
        sys.exit(1)


if __name__ == "__main__":
    main() 