#!/usr/bin/env python3
"""
Standalone Trade Ledger File Watcher (TYU5 P&L Pipeline)

This script runs only the trade ledger file watcher which:
1. Monitors for new trade ledger CSV files in data/input/trade_ledger/
2. Triggers the TYU5 P&L pipeline when files are created/modified
3. Also monitors market prices database for updates
4. Monitors spot risk CSV files to trigger FULLPNL updates

The pipeline:
- Processes trades through TradePreprocessor
- Runs FIFO P&L calculations
- Updates database tables: tyu5_trades, tyu5_positions, tyu5_pnl_components
- Updates FULLPNL table when spot risk files change

Database output:
- data/output/pnl/pnl_tracker.db
"""

import sys
import logging
import signal
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_integration.pnl_pipeline_watcher import PNLPipelineWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run trade ledger watcher."""
    
    # Banner
    print("=" * 60)
    print("TRADE LEDGER FILE WATCHER (TYU5 P&L Pipeline)")
    print("=" * 60)
    print("This watcher monitors for:")
    print("  1. Trade ledger CSV files")
    print("  2. Market price database updates")
    print("  3. Spot risk CSV files (for FULLPNL updates)")
    print()
    print("Monitoring directories:")
    print("  - Trade ledger: data/input/trade_ledger/")
    print("  - Market prices: data/output/market_prices/market_prices.db")
    print("  - Spot risk: data/output/spot_risk/")
    print()
    print("Output:")
    print("  - Database: data/output/pnl/pnl_tracker.db")
    print("  - Tables: tyu5_trades, tyu5_positions, tyu5_pnl_components, FULLPNL")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Initialize watcher
    watcher = None
    
    try:
        # Create watcher with default paths
        watcher = PNLPipelineWatcher(
            trade_ledger_dir="data/input/trade_ledger",
            market_prices_db="data/output/market_prices/market_prices.db",
            spot_risk_dir="data/output/spot_risk"
        )
        
        # Signal handler for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received...")
            if watcher:
                watcher.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the watcher
        logger.info("Starting Trade Ledger File Watcher...")
        watcher.start()
        logger.info("Trade Ledger File Watcher started successfully")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in trade ledger watcher: {e}", exc_info=True)
    finally:
        if watcher:
            try:
                watcher.stop()
                logger.info("Trade Ledger Watcher stopped")
            except Exception as e:
                logger.error(f"Error stopping watcher: {e}")

if __name__ == "__main__":
    main() 