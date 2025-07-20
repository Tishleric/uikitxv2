#!/usr/bin/env python3
"""
Test script to verify spot risk price updates to market prices database.

This script:
1. Processes a spot risk CSV file
2. Updates Current_Price in market prices database
3. Displays the results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from datetime import datetime
import sqlite3

from lib.trading.market_prices import MarketPriceStorage, SpotRiskPriceProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test spot risk price update functionality."""
    
    logger.info("="*60)
    logger.info("TESTING SPOT RISK PRICE UPDATE")
    logger.info("="*60)
    
    # Find a recent spot risk file
    spot_risk_dir = Path("data/input/actant_spot_risk")
    csv_files = []
    
    # Look for files in date subdirectories and root
    for pattern in ["*/bav_analysis_*.csv", "bav_analysis_*.csv"]:
        csv_files.extend(spot_risk_dir.glob(pattern))
    
    if not csv_files:
        logger.error(f"No spot risk CSV files found in {spot_risk_dir}")
        return
        
    # Sort by modification time and get the most recent
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    test_file = csv_files[0]
    
    logger.info(f"Using test file: {test_file}")
    logger.info(f"File date: {datetime.fromtimestamp(test_file.stat().st_mtime)}")
    
    # Initialize components
    storage = MarketPriceStorage()
    processor = SpotRiskPriceProcessor(storage)
    
    # Process the file
    logger.info("\nProcessing file...")
    success = processor.process_file(test_file)
    
    if success:
        logger.info("✓ File processed successfully")
    else:
        logger.error("✗ Failed to process file")
        return
        
    # Check the database for updated prices
    logger.info("\nChecking database for Current_Price updates...")
    
    db_path = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check futures with Current_Price
    cursor.execute("""
        SELECT symbol, Current_Price, last_updated
        FROM futures_prices
        WHERE Current_Price IS NOT NULL
        ORDER BY last_updated DESC
        LIMIT 10
    """)
    
    futures_rows = cursor.fetchall()
    logger.info(f"\nFutures with Current_Price: {len(futures_rows)}")
    for row in futures_rows[:5]:  # Show first 5
        logger.info(f"  {row[0]}: ${row[1]:.4f} (updated: {row[2]})")
        
    # Check options with Current_Price
    cursor.execute("""
        SELECT symbol, Current_Price, last_updated
        FROM options_prices
        WHERE Current_Price IS NOT NULL
        ORDER BY last_updated DESC
        LIMIT 10
    """)
    
    options_rows = cursor.fetchall()
    logger.info(f"\nOptions with Current_Price: {len(options_rows)}")
    for row in options_rows[:5]:  # Show first 5
        logger.info(f"  {row[0]}: ${row[1]:.4f} (updated: {row[2]})")
        
    # Summary statistics
    cursor.execute("SELECT COUNT(*) FROM futures_prices WHERE Current_Price IS NOT NULL")
    total_futures = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM options_prices WHERE Current_Price IS NOT NULL")
    total_options = cursor.fetchone()[0]
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total futures with Current_Price: {total_futures}")
    logger.info(f"Total options with Current_Price: {total_options}")
    logger.info(f"Grand total: {total_futures + total_options}")
    
    conn.close()


if __name__ == "__main__":
    main() 