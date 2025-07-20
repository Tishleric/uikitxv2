#!/usr/bin/env python3
"""
Recreate market prices database with updated schema including Current_Price column.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices import MarketPriceStorage

def recreate_database():
    """Drop and recreate the market prices database."""
    print("Recreating market prices database with updated schema...")
    
    # Initialize storage - this will create tables with new schema
    storage = MarketPriceStorage()
    
    print(f"Database recreated at: {storage.db_path}")
    print("\nNew schema includes:")
    print("- Current_Price column (for spot risk data)")
    print("- Flash_Close column (for 2pm files)")
    print("- prior_close column (for 4pm files)")
    print("- All symbols stored with 'Comdty' suffix")
    
    # Verify tables were created
    with storage._get_connection() as conn:
        cursor = conn.cursor()
        
        # Check futures table
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='futures_prices'
        """)
        futures_schema = cursor.fetchone()
        if futures_schema:
            print("\nFutures table schema:")
            print(futures_schema[0])
            
        # Check options table
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='options_prices'
        """)
        options_schema = cursor.fetchone()
        if options_schema:
            print("\nOptions table schema:")
            print(options_schema[0])

if __name__ == "__main__":
    recreate_database() 