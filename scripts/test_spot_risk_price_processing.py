#!/usr/bin/env python3
"""
Test spot risk price processing to debug why options aren't getting current prices.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
import pandas as pd

from lib.trading.market_prices import MarketPriceStorage, SpotRiskPriceProcessor
from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test spot risk price processing."""
    
    logger.info("="*60)
    logger.info("TESTING SPOT RISK PRICE PROCESSING")
    logger.info("="*60)
    
    # Find a recent spot risk file
    test_file = Path("data/input/actant_spot_risk/2025-07-18/bav_analysis_20250717_145100.csv")
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return
        
    logger.info(f"Using test file: {test_file}")
    
    # Test symbol translation first
    logger.info("\n" + "="*60)
    logger.info("TESTING SYMBOL TRANSLATION")
    logger.info("="*60)
    
    translator = SpotRiskSymbolTranslator()
    
    # Read CSV to get sample symbols
    df = pd.read_csv(test_file)
    df = df.iloc[1:].reset_index(drop=True)  # Skip type row
    
    # Test a few symbols
    test_symbols = [
        "XCME.ZN.SEP25",  # Future
        "XCME.VY3.21JUL25.111.C",  # Option
        "XCME.ZN3.18JUL25.111.P",  # Friday option
        "XCME.WY3.16JUL25.111.C",  # Wednesday option
    ]
    
    for symbol in test_symbols:
        bloomberg = translator.translate(symbol)
        logger.info(f"{symbol} → {bloomberg}")
    
    # Now test the full price processor
    logger.info("\n" + "="*60)
    logger.info("TESTING PRICE EXTRACTION")
    logger.info("="*60)
    
    storage = MarketPriceStorage()
    processor = SpotRiskPriceProcessor(storage)
    
    # Process the file
    success = processor.process_file(test_file)
    
    if success:
        logger.info("✓ File processed successfully")
        
        # Query the database to see what was stored
        logger.info("\n" + "="*60)
        logger.info("CHECKING DATABASE RESULTS")
        logger.info("="*60)
        
        import sqlite3
        conn = sqlite3.connect(str(storage.db_path))
        
        # Check futures
        logger.info("\nFutures with Current_Price:")
        cursor = conn.execute("""
            SELECT symbol, Current_Price, trade_date
            FROM futures_prices
            WHERE Current_Price IS NOT NULL
            ORDER BY symbol
            LIMIT 10
        """)
        for row in cursor:
            logger.info(f"  {row[0]}: ${row[1]:.4f} ({row[2]})")
            
        # Check options
        logger.info("\nOptions with Current_Price:")
        cursor = conn.execute("""
            SELECT symbol, Current_Price, trade_date
            FROM options_prices
            WHERE Current_Price IS NOT NULL
            ORDER BY symbol
            LIMIT 10
        """)
        for row in cursor:
            logger.info(f"  {row[0]}: ${row[1]:.4f} ({row[2]})")
            
        # Count total
        cursor = conn.execute("SELECT COUNT(*) FROM options_prices WHERE Current_Price IS NOT NULL")
        opt_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM futures_prices WHERE Current_Price IS NOT NULL")
        fut_count = cursor.fetchone()[0]
        
        logger.info(f"\nTotal futures with Current_Price: {fut_count}")
        logger.info(f"Total options with Current_Price: {opt_count}")
        
        conn.close()
    else:
        logger.error("✗ Failed to process file")


if __name__ == "__main__":
    main() 