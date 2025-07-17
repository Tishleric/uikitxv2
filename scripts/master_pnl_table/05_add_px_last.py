#!/usr/bin/env python3
"""
05_add_px_last.py

Adds px_last column to FULLPNL table from market_prices database.
Maps current_price for both futures and options.
"""

import sqlite3
import os
import pandas as pd
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def add_px_last_column(conn: sqlite3.Connection) -> None:
    """Add px_last column to FULLPNL if it doesn't exist."""
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(FULLPNL)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'px_last' not in columns:
        cursor.execute("ALTER TABLE FULLPNL ADD COLUMN px_last REAL")
        logger.info("Added px_last column to FULLPNL")
    else:
        logger.info("px_last column already exists")
    
    conn.commit()


def inspect_market_prices_structure(market_db_path: str) -> None:
    """Inspect the structure of market_prices database."""
    conn = sqlite3.connect(market_db_path)
    cursor = conn.cursor()
    
    try:
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Tables in market_prices.db: {[t[0] for t in tables]}")
        
        # Check futures_prices structure
        cursor.execute("PRAGMA table_info(futures_prices)")
        futures_cols = cursor.fetchall()
        logger.info("futures_prices columns:")
        for col in futures_cols:
            logger.info(f"  {col[1]} ({col[2]})")
            
        # Check options_prices structure if exists
        if any(t[0] == 'options_prices' for t in tables):
            cursor.execute("PRAGMA table_info(options_prices)")
            options_cols = cursor.fetchall()
            logger.info("options_prices columns:")
            for col in options_cols:
                logger.info(f"  {col[1]} ({col[2]})")
        
        # Sample data
        cursor.execute("SELECT * FROM futures_prices LIMIT 3")
        futures_sample = cursor.fetchall()
        logger.info(f"Sample futures_prices: {futures_sample}")
        
    finally:
        conn.close()


def get_market_prices(market_db_path: str, symbols: list) -> Dict[str, float]:
    """Get current_price from market_prices database for given symbols."""
    conn = sqlite3.connect(market_db_path)
    cursor = conn.cursor()
    
    prices = {}
    
    try:
        # First, let's see what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        logger.info(f"Available tables: {tables}")
        
        # Process each symbol
        for symbol in symbols:
            # Check if it's an option (has strike price)
            parts = symbol.replace(' Comdty', '').split()
            
            if len(parts) == 2:
                # Option format: "VBYN25P3 110.250 Comdty" 
                # Try options_prices table first with full symbol
                if 'options_prices' in tables:
                    cursor.execute("""
                        SELECT symbol, current_price 
                        FROM options_prices 
                        WHERE symbol = ?
                        ORDER BY last_updated DESC
                        LIMIT 1
                    """, (symbol,))
                    result = cursor.fetchone()
                    if result:
                        prices[symbol] = result[1]
                        logger.info(f"Found option price: {symbol} -> {result[1]}")
                        continue
            
            # Future format: "TYU5 Comdty"
            # Try without " Comdty" suffix
            symbol_without_comdty = symbol.replace(' Comdty', '')
            cursor.execute("""
                SELECT symbol, current_price 
                FROM futures_prices 
                WHERE symbol = ?
                ORDER BY last_updated DESC
                LIMIT 1
            """, (symbol_without_comdty,))
            result = cursor.fetchone()
            if result:
                prices[symbol] = result[1]
                logger.info(f"Found future price: {symbol} -> {result[1]} (matched as {symbol_without_comdty})")
                continue
                
            # Also try with full symbol in futures table
            cursor.execute("""
                SELECT symbol, current_price 
                FROM futures_prices 
                WHERE symbol = ?
                ORDER BY last_updated DESC
                LIMIT 1
            """, (symbol,))
            result = cursor.fetchone()
            if result:
                prices[symbol] = result[1]
                logger.info(f"Found future price: {symbol} -> {result[1]}")
        
        # If we didn't find exact matches, let's see what symbols are in the database
        if len(prices) < len(symbols):
            logger.info("Checking available symbols in database...")
            cursor.execute("SELECT DISTINCT symbol FROM futures_prices LIMIT 20")
            available_symbols = [row[0] for row in cursor.fetchall()]
            logger.info(f"Sample symbols in futures_prices: {available_symbols}")
            
            if 'options_prices' in tables:
                cursor.execute("SELECT DISTINCT symbol FROM options_prices LIMIT 20")
                available_options = [row[0] for row in cursor.fetchall()]
                logger.info(f"Sample symbols in options_prices: {available_options}")
    
    finally:
        conn.close()
    
    return prices


def update_fullpnl_with_px_last(conn: sqlite3.Connection, prices: Dict[str, float]) -> int:
    """Update FULLPNL table with px_last data."""
    cursor = conn.cursor()
    
    updates = 0
    for symbol, price in prices.items():
        if price is not None:
            cursor.execute("""
                UPDATE FULLPNL 
                SET px_last = ?
                WHERE symbol = ?
            """, (price, symbol))
            
            if cursor.rowcount > 0:
                updates += cursor.rowcount
                logger.debug(f"Updated {symbol}: px_last={price}")
    
    conn.commit()
    logger.info(f"Updated {updates} rows with px_last data")
    return updates


def display_results(conn: sqlite3.Connection) -> None:
    """Display the updated FULLPNL table."""
    cursor = conn.cursor()
    
    print("\nUpdated FULLPNL Table with px_last:")
    print("=" * 140)
    print(f"{'Symbol':<30} {'Bid':>10} {'Ask':>10} {'Price':>10} {'PX Last':>10} {'Diff':>10}")
    print("-" * 140)
    
    cursor.execute("""
        SELECT symbol, bid, ask, price, px_last,
               CASE WHEN price IS NOT NULL AND px_last IS NOT NULL 
                    THEN px_last - price 
                    ELSE NULL 
               END as diff
        FROM FULLPNL 
        ORDER BY symbol
    """)
    
    for row in cursor.fetchall():
        symbol, bid, ask, price, px_last, diff = row
        
        bid_str = f"{bid:.6f}" if bid is not None else "NULL"
        ask_str = f"{ask:.6f}" if ask is not None else "NULL"
        price_str = f"{price:.6f}" if price is not None else "NULL"
        px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
        diff_str = f"{diff:.6f}" if diff is not None else "NULL"
        
        print(f"{symbol:<30} {bid_str:>10} {ask_str:>10} {price_str:>10} {px_last_str:>10} {diff_str:>10}")
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(px_last) as with_px_last,
            COUNT(CASE WHEN price IS NOT NULL AND px_last IS NOT NULL THEN 1 END) as with_both
        FROM FULLPNL
    """)
    
    total, with_px_last, with_both = cursor.fetchone()
    print("\nSummary:")
    print(f"  Total symbols: {total}")
    print(f"  With px_last data: {with_px_last} ({with_px_last/total*100:.1f}%)")
    print(f"  With both price and px_last: {with_both} ({with_both/total*100:.1f}%)")


def main():
    """Main function to add px_last to FULLPNL."""
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    pnl_db_path = os.path.join(project_root, "data", "output", "pnl", "pnl_tracker.db")
    market_db_path = os.path.join(project_root, "data", "output", "market_prices", "market_prices.db")
    
    # Check if market_prices database exists
    if not os.path.exists(market_db_path):
        logger.error(f"Market prices database not found at {market_db_path}")
        return
    
    logger.info(f"Using market prices database: {market_db_path}")
    
    # First inspect the market_prices structure
    inspect_market_prices_structure(market_db_path)
    
    # Connect to pnl database
    conn = sqlite3.connect(pnl_db_path)
    
    try:
        # Add column if needed
        add_px_last_column(conn)
        
        # Get all symbols from FULLPNL
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM FULLPNL")
        symbols = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(symbols)} symbols in FULLPNL to look up")
        
        # Get market prices
        prices = get_market_prices(market_db_path, symbols)
        logger.info(f"Found {len(prices)} market prices")
        
        if prices:
            update_fullpnl_with_px_last(conn, prices)
        else:
            logger.warning("No market prices found for any symbols")
        
        # Display results
        display_results(conn)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("Adding px_last column to FULLPNL from market_prices")
    print("=" * 60)
    main() 