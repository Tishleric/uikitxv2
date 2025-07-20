#!/usr/bin/env python3
"""
Add Current_Price column to market prices database tables.

This script adds the Current_Price column to both futures_prices and options_prices tables
to support storing real-time prices from spot risk files.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_current_price_column():
    """Add Current_Price column to market prices tables."""
    
    # Path to market prices database
    db_path = Path("data/output/market_prices/market_prices.db")
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
        
    logger.info(f"Adding Current_Price column to database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current schema
        logger.info("\nChecking current schema...")
        
        # Get futures_prices columns
        cursor.execute("PRAGMA table_info(futures_prices)")
        futures_cols = {row[1]: row[2] for row in cursor.fetchall()}
        logger.info(f"Futures columns: {list(futures_cols.keys())}")
        
        # Get options_prices columns  
        cursor.execute("PRAGMA table_info(options_prices)")
        options_cols = {row[1]: row[2] for row in cursor.fetchall()}
        logger.info(f"Options columns: {list(options_cols.keys())}")
        
        # Add Current_Price to futures_prices if it doesn't exist
        if 'Current_Price' not in futures_cols:
            logger.info("\nAdding Current_Price to futures_prices table...")
            cursor.execute("""
                ALTER TABLE futures_prices 
                ADD COLUMN Current_Price REAL
            """)
            logger.info("✓ Added Current_Price column to futures_prices")
        else:
            logger.info("✓ Current_Price already exists in futures_prices")
            
        # Add Current_Price to options_prices if it doesn't exist
        if 'Current_Price' not in options_cols:
            logger.info("\nAdding Current_Price to options_prices table...")
            cursor.execute("""
                ALTER TABLE options_prices 
                ADD COLUMN Current_Price REAL
            """)
            logger.info("✓ Added Current_Price column to options_prices")
        else:
            logger.info("✓ Current_Price already exists in options_prices")
            
        # Commit changes
        conn.commit()
        
        # Verify the columns were added
        logger.info("\nVerifying schema after update...")
        
        cursor.execute("PRAGMA table_info(futures_prices)")
        futures_cols = [row[1] for row in cursor.fetchall()]
        logger.info(f"Futures columns after update: {futures_cols}")
        
        cursor.execute("PRAGMA table_info(options_prices)")
        options_cols = [row[1] for row in cursor.fetchall()]
        logger.info(f"Options columns after update: {options_cols}")
        
        conn.close()
        
        logger.info("\n✓ Successfully updated database schema")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        return False


def main():
    """Main entry point."""
    logger.info("="*60)
    logger.info("MARKET PRICES DATABASE SCHEMA UPDATE")
    logger.info("="*60)
    
    success = add_current_price_column()
    
    if success:
        logger.info("\n✓ Database schema updated successfully")
        logger.info("The spot risk file watcher can now update Current_Price values")
    else:
        logger.error("\n✗ Failed to update database schema")
        sys.exit(1)


if __name__ == "__main__":
    main() 