#!/usr/bin/env python
"""Populate market prices from existing CSV files into the database."""

import sys
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.service import PnLService
from lib.trading.pnl_calculator.storage import PnLStorage
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_price_files():
    """Process all existing price files into the market_prices table."""
    
    # Initialize storage and service
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    service = PnLService(storage)
    
    # Price directories
    price_dirs = [
        Path("data/input/market_prices/futures"),
        Path("data/input/market_prices/options")
    ]
    
    total_processed = 0
    
    for price_dir in price_dirs:
        if not price_dir.exists():
            logger.warning(f"Directory not found: {price_dir}")
            continue
            
        logger.info(f"\nProcessing files from: {price_dir}")
        
        # Get all CSV files
        csv_files = sorted(price_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            logger.info(f"Processing: {csv_file.name}")
            
            try:
                # Process the file through the service
                service.process_market_price_file(str(csv_file))
                total_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                
    logger.info(f"\nCompleted! Processed {total_processed} price files.")
    
    # Check what's in the database
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM market_prices")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT bloomberg) FROM market_prices")
    unique_symbols = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT upload_date) FROM market_prices")
    unique_dates = cursor.fetchone()[0]
    
    logger.info(f"\nDatabase now contains:")
    logger.info(f"  Total price records: {count}")
    logger.info(f"  Unique symbols: {unique_symbols}")
    logger.info(f"  Unique dates: {unique_dates}")
    
    # Show sample data
    cursor.execute("""
        SELECT bloomberg, asset_type, px_last, px_settle, upload_timestamp
        FROM market_prices
        ORDER BY upload_timestamp DESC
        LIMIT 5
    """)
    
    logger.info("\nSample price records:")
    for row in cursor.fetchall():
        logger.info(f"  {row['bloomberg']} ({row['asset_type']}): last={row['px_last']}, settle={row['px_settle']}, time={row['upload_timestamp']}")
    
    conn.close()

if __name__ == "__main__":
    process_price_files() 