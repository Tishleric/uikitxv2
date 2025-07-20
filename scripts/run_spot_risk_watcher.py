#!/usr/bin/env python3
"""
Run the Spot Risk File Watcher

This script monitors the actant_spot_risk directory for new CSV files and:
1. Processes them for Greek calculations
2. Updates Current_Price in the market_prices database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import signal
import logging
import time
from pathlib import Path

from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for the watcher
watcher = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping watcher...")
    if watcher:
        watcher.stop()
    sys.exit(0)

def main():
    """Main entry point."""
    global watcher
    
    logger.info("="*60)
    logger.info("SPOT RISK FILE WATCHER")
    logger.info("="*60)
    
    # Set up directories
    input_dir = Path("data/input/actant_spot_risk")
    output_dir = Path("data/output/spot_risk/processed")
    
    # Create directories if they don't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Watching directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("")
    logger.info("This watcher will:")
    logger.info("  - Monitor for new bav_analysis_*.csv files")
    logger.info("  - Calculate Greeks and other analytics")
    logger.info("  - Update Current_Price in market_prices.db")
    logger.info("")
    logger.info("Press Ctrl+C to stop...")
    logger.info("="*60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and start the watcher
    watcher = SpotRiskWatcher(
        input_dir=str(input_dir),
        output_dir=str(output_dir)
    )
    
    # Start watching
    watcher.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)  # Sleep for 1 minute
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("\nShutting down watcher...")
        watcher.stop()
        logger.info("Watcher stopped.")

if __name__ == "__main__":
    main() 