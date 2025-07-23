#!/usr/bin/env python3
"""
Standalone Market Price File Monitor

This script runs only the market price file monitor which:
1. Watches for futures and options CSV files
2. Processes them to extract flash close (2pm) and prior close (4pm) prices
3. Stores the data in market_prices.db

The monitor watches:
- data/input/market_prices/futures/ for futures files
- data/input/market_prices/options/ for options files
"""

import sys
import logging
import signal
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.market_prices import MarketPriceFileMonitor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global monitor instance
monitor = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal, stopping monitor...")
    if monitor and monitor.is_monitoring():
        monitor.stop()
    sys.exit(0)

def main():
    """Run the market price file monitor."""
    global monitor
    
    print("=" * 60)
    print("MARKET PRICE FILE MONITOR")
    print("=" * 60)
    print("\nThis monitor processes market price files to extract:")
    print("  - Flash Close prices (2pm CDT)")
    print("  - Prior Close prices (4pm CDT)")
    print("\nMonitoring directories:")
    print("  - Futures: data/input/market_prices/futures/")
    print("  - Options: data/input/market_prices/options/")
    print("\nDatabase: data/output/market_prices/market_prices.db")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create monitor instance
        monitor = MarketPriceFileMonitor()
        
        # Process any existing files first
        logger.info("\nChecking for existing files to process...")
        monitor.process_existing_files()
        
        # Start monitoring
        logger.info("\nStarting file monitor...")
        monitor.start()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in market price monitor: {e}", exc_info=True)
    finally:
        if monitor and monitor.is_monitoring():
            monitor.stop()

if __name__ == "__main__":
    main() 