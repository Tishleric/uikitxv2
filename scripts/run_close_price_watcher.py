#!/usr/bin/env python3
"""
Run the close price watcher for trades.db

Monitors Z:\\Trade_Control\\Futures and Z:\\Trade_Control\\Options for new CSV files
and updates close prices in trades.db

The watcher:
- Processes new CSV files only (ignores existing files)
- Calls roll_2pm_prices for every CSV received
- Triggers roll_4pm_prices at 4pm CDT if all files received, or at 4:30pm CDT as fallback
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import signal
from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceWatcher

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
    parser = argparse.ArgumentParser(description='Close Price Watcher for trades.db')
    parser.add_argument('--db', default='trades.db', help='Path to trades database')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Update log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run watcher
    logger.info("=" * 60)
    logger.info("Close Price Watcher Starting")
    logger.info("=" * 60)
    logger.info(f"Database: {args.db}")
    logger.info("Configuration:")
    logger.info(r"  - Monitoring Z:\Trade_Control\Futures")
    logger.info(r"  - Monitoring Z:\Trade_Control\Options")
    logger.info("  - Processing new files only (no historical)")
    logger.info("  - Calling roll_2pm_prices for every CSV")
    logger.info("  - 4pm roll triggers:")
    logger.info("    - At 4:00pm CDT if all files received")
    logger.info("    - At 4:30pm CDT if 4pm file received (fallback)")
    logger.info("")
    
    global watcher
    watcher = ClosePriceWatcher(db_path=args.db)
    
    try:
        watcher.run_forever()
    except Exception as e:
        logger.error(f"Error running watcher: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main()) 