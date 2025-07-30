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
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher
from lib.monitoring.decorators import monitor, start_observatory_writer, stop_observatory_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Directories
INPUT_DIR = "data/input/actant_spot_risk"
OUTPUT_DIR = "data/output/spot_risk"


@monitor()
def main():
    """Main entry point for the watcher service."""
    print("="*60)
    print("Spot Risk File Watcher Service")
    print("="*60)
    print(f"\nMonitoring: {INPUT_DIR}")
    print(f"Output to: {OUTPUT_DIR}")
    print("\nPress Ctrl+C to stop\n")
    
    # Reserve cores for other processes. A safe number is N-4.
    # Ensure we use at least 1 worker.
    num_workers = max(1, os.cpu_count() - 4)
    print(f"Initializing with {num_workers} worker processes...")

    # Create watcher
    watcher = SpotRiskWatcher(input_dir=INPUT_DIR, num_workers=num_workers)
    
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
    # Start the observatory writer for monitoring
    print("Starting observatory writer...")
    start_observatory_writer(db_path="logs/observatory.db")
    
    try:
        main()
    finally:
        # Stop the observatory writer on exit
        stop_observatory_writer() 