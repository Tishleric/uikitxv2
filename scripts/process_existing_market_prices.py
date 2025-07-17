#!/usr/bin/env python3
"""
Script to process all existing market price files.

This will populate the market_prices.db with all CSV files currently
in the data/input/market_prices/futures and options directories.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor, OptionsProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Process all existing market price files."""
    logger.info("="*60)
    logger.info("PROCESSING EXISTING MARKET PRICE FILES")
    logger.info("="*60)
    
    # Initialize storage and processors
    storage = MarketPriceStorage()
    futures_processor = FuturesProcessor(storage)
    options_processor = OptionsProcessor(storage)
    
    # Set up directories
    data_root = Path(__file__).parent.parent
    futures_dir = data_root / "data" / "input" / "market_prices" / "futures"
    options_dir = data_root / "data" / "input" / "market_prices" / "options"
    
    # Process futures files
    logger.info(f"\nProcessing futures files from: {futures_dir}")
    futures_files = sorted(futures_dir.glob("*.csv"))
    futures_success = 0
    futures_failed = 0
    
    for filepath in futures_files:
        logger.info(f"\nProcessing: {filepath.name}")
        try:
            if futures_processor.process_file(filepath):
                futures_success += 1
            else:
                futures_failed += 1
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
            futures_failed += 1
    
    # Process options files
    logger.info(f"\n\nProcessing options files from: {options_dir}")
    options_files = sorted(options_dir.glob("*.csv"))
    options_success = 0
    options_failed = 0
    
    for filepath in options_files:
        logger.info(f"\nProcessing: {filepath.name}")
        try:
            if options_processor.process_file(filepath):
                options_success += 1
            else:
                options_failed += 1
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
            options_failed += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*60)
    logger.info(f"Futures: {futures_success} successful, {futures_failed} failed out of {len(futures_files)} total")
    logger.info(f"Options: {options_success} successful, {options_failed} failed out of {len(options_files)} total")
    
    # Check database
    db_path = data_root / "data" / "output" / "market_prices" / "market_prices.db"
    
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM futures_prices")
    futures_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM options_prices")
    options_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM price_file_tracker")
    files_tracked = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"\nDatabase contents:")
    logger.info(f"  - {futures_count} futures price records")
    logger.info(f"  - {options_count} options price records")
    logger.info(f"  - {files_tracked} files tracked")

if __name__ == "__main__":
    main() 