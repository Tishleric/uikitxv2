#!/usr/bin/env python3
"""
Main script to run the market price file monitoring system.

This script monitors the market_prices/futures and market_prices/options directories
for new price files and processes them according to the time windows (2pm and 4pm CDT).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import signal
import logging
import time
from lib.trading.market_prices import MarketPriceFileMonitor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for the monitor
monitor = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping monitor...")
    if monitor:
        monitor.stop()
    sys.exit(0)

def main():
    """Main entry point."""
    global monitor
    
    logger.info("="*60)
    logger.info("MARKET PRICE FILE MONITOR")
    logger.info("="*60)
    logger.info("Monitoring directories:")
    logger.info("  - data/input/market_prices/futures/")
    logger.info("  - data/input/market_prices/options/")
    logger.info("")
    logger.info("Processing windows:")
    logger.info("  - 2:00 PM CDT ± 15 minutes: Updates current prices")
    logger.info("  - 4:00 PM CDT ± 15 minutes: Sets next day's prior close")
    logger.info("  - 3:00 PM files are ignored")
    logger.info("")
    logger.info("Press Ctrl+C to stop...")
    logger.info("="*60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and start the monitor
    monitor = MarketPriceFileMonitor()
    
    # Optional callbacks for notification
    def futures_callback(filepath, result):
        if result:
            logger.info(f"✓ Processed futures file: {filepath.name}")
        else:
            logger.warning(f"✗ Failed to process futures file: {filepath.name}")
    
    def options_callback(filepath, result):
        if result:
            logger.info(f"✓ Processed options file: {filepath.name}")
        else:
            logger.warning(f"✗ Failed to process options file: {filepath.name}")
    
    monitor.futures_callback = futures_callback
    monitor.options_callback = options_callback
    
    # Start monitoring
    monitor.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)  # Sleep for 1 minute
            # Could add periodic status checks here
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("\nShutting down monitor...")
        monitor.stop()
        logger.info("Monitor stopped.")

if __name__ == "__main__":
    main() 