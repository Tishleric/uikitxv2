#!/usr/bin/env python3
"""
Run Spot Risk Price Watcher for PnL System

Purpose: Monitor spot risk CSV files and update current prices in trades.db
"""

import sys
import logging
import argparse
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_fifo_lifo import SpotRiskPriceWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Monitor spot risk files and update current prices in trades.db'
    )
    parser.add_argument(
        '--db', 
        default='trades.db',
        help='Path to trades.db database (default: trades.db in root folder)'
    )
    parser.add_argument(
        '--input-dir',
        default='data/input/actant_spot_risk',
        help='Directory to watch for spot risk CSV files (default: data/input/actant_spot_risk)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Resolve paths
    db_path = Path(args.db).resolve()
    input_dir = Path(args.input_dir).resolve()
    
    # Validate paths
    if not db_path.parent.exists():
        logger.error(f"Database directory does not exist: {db_path.parent}")
        return 1
        
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        logger.info(f"Creating directory: {input_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and run watcher
    logger.info("=" * 60)
    logger.info("Spot Risk Price Watcher for PnL System")
    logger.info("=" * 60)
    logger.info(f"Database: {db_path}")
    logger.info(f"Input directory: {input_dir}")
    logger.info("=" * 60)
    
    try:
        watcher = SpotRiskPriceWatcher(str(db_path), str(input_dir))
        logger.info("Starting file watcher... Press Ctrl+C to stop")
        watcher.run_forever()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main()) 