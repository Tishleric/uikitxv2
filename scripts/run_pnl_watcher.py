#!/usr/bin/env python3
"""
Run the PNL Pipeline Watcher service.

This script monitors for changes in:
- Trade ledger CSV files
- Market prices database

And automatically triggers the TYU5 P&L calculation pipeline.

Usage:
    python scripts/run_pnl_watcher.py

Press Ctrl+C to stop the watcher.
"""

import sys
import time
import signal
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_integration.pnl_pipeline_watcher import PNLPipelineWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Global watcher instance for signal handling
watcher = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("\nShutdown signal received...")
    if watcher:
        watcher.stop()
    sys.exit(0)


def main():
    """Main entry point for the watcher service."""
    global watcher
    
    print("=" * 80)
    print("PNL Pipeline Watcher Service")
    print("=" * 80)
    print("\nMonitoring:")
    print("  - Trade ledgers: data/input/trade_ledger/")
    print("  - Market prices: data/output/market_prices/market_prices.db")
    print("\nDebounce interval: 10 seconds")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start watcher
        watcher = PNLPipelineWatcher()
        watcher.start()
        
        print("\nWatcher is running...")
        print("Waiting for changes...\n")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down watcher...")
        if watcher:
            watcher.stop()
        print("Watcher stopped.")
    except Exception as e:
        logger.error(f"Error in watcher service: {e}")
        if watcher:
            watcher.stop()
        sys.exit(1)


if __name__ == "__main__":
    main() 