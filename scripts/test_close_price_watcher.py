#!/usr/bin/env python3
"""
Test script for Close Price Watcher - Safe testing without disrupting production

Usage: python scripts/test_close_price_watcher.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

from lib.trading.pnl_fifo_lifo import create_all_tables
from lib.trading.pnl_fifo_lifo.close_price_watcher import ClosePriceFileHandler
from lib.trading.pnl_fifo_lifo.config import FUTURES_SYMBOLS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_test_database(db_path):
    """Create a test database with required tables"""
    conn = sqlite3.connect(db_path)
    create_all_tables(conn)
    conn.close()
    logger.info(f"Created test database: {db_path}")


def create_test_futures_csv(output_dir, hour=14, settle=True):
    """Create a test futures CSV file"""
    filename = f"Futures_{datetime.now().strftime('%Y%m%d')}_{hour:02d}00.csv"
    filepath = output_dir / filename
    
    # Create test data matching the expected format
    data = {
        'A': ['TU', 'FV', 'TY', 'US', 'RX'],  # Symbols
        'B': [109.5, 107.25, 110.8125, 125.5, 130.25],  # Settle prices
        'C': [109.48, 107.23, 110.80, 125.48, 130.23],  # Flash prices
        'D': ['', '', '', '', ''],
        'E': ['', '', '', '', ''],
        'F': ['', '', '', '', ''],
        'G': ['', '', '', '', ''],
        'H': ['Y' if settle else 'N'] * 5  # Status column
    }
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, header=False)
    logger.info(f"Created test futures file: {filepath}")
    return filepath


def create_test_options_csv(output_dir, hour=14, settle=True):
    """Create a test options CSV file"""
    filename = f"Options_{datetime.now().strftime('%Y%m%d')}_{hour:02d}00.csv"
    filepath = output_dir / filename
    
    # Create test data with fewer rows for testing
    symbols = ['TYU5C 111 Comdty', 'TYU5P 110 Comdty', 'FVU5C 108 Comdty']
    flash_prices = [0.45, 0.32, 0.28]
    settle_prices = [0.46, 0.33, 0.29]
    
    # Create columns A-K
    data = {}
    for i in range(7):  # A-G
        data[chr(65+i)] = [''] * len(symbols)
    
    # Set G column (status)
    data['G'] = ['Y' if settle else 'N'] * len(symbols)
    
    # H is empty
    data['H'] = [''] * len(symbols)
    
    # I = symbols, J = flash, K = settle
    data['I'] = symbols
    data['J'] = flash_prices
    data['K'] = settle_prices
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, header=False)
    logger.info(f"Created test options file: {filepath}")
    return filepath


def test_file_processing():
    """Test the file processing without running the full watcher"""
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_db = temp_path / "test_trades.db"
        
        # Create test database
        create_test_database(test_db)
        
        # Create file handler
        handler = ClosePriceFileHandler(str(test_db))
        
        # Test 1: Process futures file with settle prices
        logger.info("\n=== Test 1: Futures with settle prices ===")
        futures_file = create_test_futures_csv(temp_path, hour=16, settle=True)
        handler._process_file(futures_file)
        
        # Test 2: Process futures file with flash prices
        logger.info("\n=== Test 2: Futures with flash prices ===")
        futures_file = create_test_futures_csv(temp_path, hour=14, settle=False)
        handler._process_file(futures_file)
        
        # Test 3: Process options file
        logger.info("\n=== Test 3: Options with settle prices ===")
        options_file = create_test_options_csv(temp_path, hour=16, settle=True)
        handler._process_file(options_file)
        
        # Check results in database
        logger.info("\n=== Checking database results ===")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pricing ORDER BY symbol, price_type")
        results = cursor.fetchall()
        
        logger.info("Pricing table contents:")
        for row in results:
            logger.info(f"  {row}")
        
        conn.close()
        
        logger.info("\n=== Test completed successfully! ===")


if __name__ == '__main__':
    test_file_processing() 