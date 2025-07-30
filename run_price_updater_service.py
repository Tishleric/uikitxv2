#!/usr/bin/env python
"""Run the Price Updater service.

This script runs the PriceUpdaterService in a persistent loop, listening for
newly processed Greek data from a Redis channel and updating the `pricing`
table in trades.db.

This service runs in parallel to the PositionsAggregator to ensure that
fast price updates are not blocked by slower P&L calculations.

Usage:
    python run_price_updater_service.py
    
Press Ctrl+C to stop the service.
"""

import sys
import signal
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.market_prices.price_updater_service import PriceUpdaterService
from lib.monitoring.decorators import monitor, start_observatory_writer, stop_observatory_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@monitor()
def main():
    """Main entry point for the price updater service."""
    print("="*60)
    print("Price Updater Service")
    print("="*60)
    print("\nListening for new data from Redis to update live prices...")
    print("Press Ctrl+C to stop\n")
    
    # Create service instance
    service = PriceUpdaterService()
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n\nShutting down price updater service...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start the persistent service loop
        service.run()
        
    except KeyboardInterrupt:
        print("\n\nShutting down price updater service...")
    except Exception as e:
        print(f"\nA critical error occurred: {e}")
        logging.getLogger(__name__).critical("Price updater service failed", exc_info=True)
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