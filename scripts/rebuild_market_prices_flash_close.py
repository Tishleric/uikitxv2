#!/usr/bin/env python3
"""
ACTIVE Script: Rebuild Market Prices Database with Flash_Close Column

This script:
1. Drops the existing market_prices.db
2. Recreates it with Flash_Close column instead of current_close
3. Processes all files in Z:\Trade_Control to populate the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
import sqlite3
import pandas as pd

from lib.trading.market_prices import MarketPriceFileMonitor, MarketPriceStorage
from lib.trading.market_prices.constants import MARKET_PRICES_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def rebuild_database():
    """Drop and rebuild the market prices database."""
    # Database path
    db_path = Path("data/output/market_prices/market_prices.db")
    
    logger.info(f"Dropping existing database at {db_path}")
    if db_path.exists():
        db_path.unlink()
    
    # Create new storage instance - this will create the schema with Flash_Close
    storage = MarketPriceStorage(db_path)
    logger.info("Created new database with Flash_Close column")
    
    # Check what's in the target directory
    logger.info(f"Checking directory: {MARKET_PRICES_DIR}")
    if not MARKET_PRICES_DIR.exists():
        logger.error(f"Directory does not exist: {MARKET_PRICES_DIR}")
        return
    
    # List files in futures and options subdirectories
    futures_dir = MARKET_PRICES_DIR / "futures"
    options_dir = MARKET_PRICES_DIR / "options"
    
    futures_files = list(futures_dir.glob("Futures_*.csv")) if futures_dir.exists() else []
    options_files = list(options_dir.glob("Options_*.csv")) if options_dir.exists() else []
    
    logger.info(f"Found {len(futures_files)} futures files")
    logger.info(f"Found {len(options_files)} options files")
    
    # Process all files by using processors directly
    from lib.trading.market_prices import FuturesProcessor, OptionsProcessor
    
    futures_processor = FuturesProcessor(storage)
    options_processor = OptionsProcessor(storage)
    
    # Process futures files
    for file_path in sorted(futures_files):
        logger.info(f"Processing futures file: {file_path.name}")
        try:
            futures_processor.process_file(file_path)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Process options files
    for file_path in sorted(options_files):
        logger.info(f"Processing options file: {file_path.name}")
        try:
            options_processor.process_file(file_path)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Verify the data
    verify_database(db_path)

def verify_database(db_path: Path):
    """Verify the database contents."""
    conn = sqlite3.connect(str(db_path))
    
    # Check schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(futures_prices)")
    futures_columns = [row[1] for row in cursor.fetchall()]
    logger.info(f"Futures table columns: {futures_columns}")
    
    cursor.execute("PRAGMA table_info(options_prices)")
    options_columns = [row[1] for row in cursor.fetchall()]
    logger.info(f"Options table columns: {options_columns}")
    
    # Check row counts
    cursor.execute("SELECT COUNT(*) FROM futures_prices")
    futures_count = cursor.fetchone()[0]
    logger.info(f"Futures prices rows: {futures_count}")
    
    cursor.execute("SELECT COUNT(*) FROM options_prices")
    options_count = cursor.fetchone()[0]
    logger.info(f"Options prices rows: {options_count}")
    
    # Show sample data with Flash_Close
    if futures_count > 0:
        logger.info("\nSample futures data:")
        df = pd.read_sql("SELECT * FROM futures_prices LIMIT 5", conn)
        print(df.to_string())
    
    if options_count > 0:
        logger.info("\nSample options data:")
        df = pd.read_sql("SELECT * FROM options_prices LIMIT 5", conn)
        print(df.to_string())
    
    conn.close()

def test_tyu5_format():
    """Test that TYU5 can read the market prices in expected format."""
    storage = MarketPriceStorage()
    
    # Get prices in TYU5 format
    from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
    adapter = TYU5Adapter()
    
    # Fetch and prepare market prices
    market_prices_df = adapter.get_market_prices()
    logger.info(f"\nTYU5 market prices format (first 5 rows):")
    if not market_prices_df.empty:
        print(market_prices_df.head().to_string())
        logger.info(f"Columns: {list(market_prices_df.columns)}")
        logger.info(f"Total prices: {len(market_prices_df)}")
    else:
        logger.warning("No market prices found!")

if __name__ == "__main__":
    logger.info("Starting market prices database rebuild with Flash_Close...")
    rebuild_database()
    logger.info("\nTesting TYU5 format compatibility...")
    test_tyu5_format()
    logger.info("\nDatabase rebuild complete!") 