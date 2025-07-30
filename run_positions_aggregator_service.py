#!/usr/bin/env python
"""Run the Positions Aggregator service.

This script runs the PositionsAggregator in a persistent loop, listening for
newly processed Greek data from a Redis queue and updating the master
positions table in trades.db.

This service replaces the need for the old pnl_pipeline_watcher.py.

Usage:
    python run_positions_aggregator_service.py
    
Press Ctrl+C to stop the service.
"""

import sys
import signal
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
from lib.monitoring.decorators import monitor, start_observatory_writer, stop_observatory_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@monitor()
def main():
    """Main entry point for the aggregator service."""
    print("="*60)
    print("Positions Aggregator Service")
    print("="*60)
    print("\nListening for new Greek data from Redis...")
    print("Press Ctrl+C to stop\n")
    
    # Create aggregator instance
    aggregator = PositionsAggregator()
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n\nShutting down aggregator service...")
        # The service loop will exit on its own, but we can add cleanup here if needed.
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start the persistent service loop
        aggregator.run_aggregation_service()
        
    except KeyboardInterrupt:
        print("\n\nShutting down aggregator service...")
    except Exception as e:
        print(f"\nA critical error occurred: {e}")
        logging.getLogger(__name__).critical("Aggregator service failed", exc_info=True)
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