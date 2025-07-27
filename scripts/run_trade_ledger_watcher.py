#!/usr/bin/env python3
"""
Run Trade Ledger Watcher for PnL System

Usage:
    python run_trade_ledger_watcher.py [--db path/to/trades.db] [--watch-dir path/to/trade/ledger]
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_fifo_lifo.trade_ledger_watcher import TradeLedgerWatcher
from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables
from lib.trading.pnl_fifo_lifo.config import DB_NAME
import sqlite3


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('trade_ledger_watcher.log')
        ]
    )


def ensure_database_exists(db_path: str):
    """Ensure database exists with all required tables."""
    conn = sqlite3.connect(db_path)
    
    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='processed_files'
    """)
    
    if not cursor.fetchone():
        logging.info("Creating database tables...")
        create_all_tables(conn)
    
    conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run Trade Ledger Watcher for PnL System')
    parser.add_argument(
        '--db', 
        default=DB_NAME,
        help='Path to trades database (default: trades.db)'
    )
    parser.add_argument(
        '--watch-dir',
        default='data/input/trade_ledger',
        help='Directory to watch for trade CSV files'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    
    # Ensure database exists
    ensure_database_exists(args.db)
    
    # Create and start watcher
    logger.info(f"Starting Trade Ledger Watcher")
    logger.info(f"Database: {args.db}")
    logger.info(f"Watch directory: {args.watch_dir}")
    
    try:
        watcher = TradeLedgerWatcher(args.db, args.watch_dir)
        watcher.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 