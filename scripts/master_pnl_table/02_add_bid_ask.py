#!/usr/bin/env python3
"""
02_add_bid_ask.py

Adds bid and ask columns to FULLPNL table by joining with spot risk data.
Designed to be reusable for automation.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_database_paths():
    """Get paths to required databases."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    paths = {
        'pnl_tracker': os.path.join(project_root, "data", "output", "pnl", "pnl_tracker.db"),
        'spot_risk': os.path.join(project_root, "data", "output", "spot_risk", "spot_risk.db"),
        'spot_risk_csv_dir': os.path.join(project_root, "data", "output", "spot_risk", "2025-07-18")
    }
    
    return paths


def add_bid_ask_columns(conn):
    """Add bid and ask columns to FULLPNL if they don't exist."""
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(FULLPNL)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'bid' not in columns:
        cursor.execute("ALTER TABLE FULLPNL ADD COLUMN bid REAL")
        logger.info("Added bid column to FULLPNL")
    else:
        logger.info("bid column already exists")
    
    if 'ask' not in columns:
        cursor.execute("ALTER TABLE FULLPNL ADD COLUMN ask REAL")
        logger.info("Added ask column to FULLPNL")
    else:
        logger.info("ask column already exists")
    
    conn.commit()


def update_bid_ask_from_csv(conn, csv_path):
    """Update bid/ask values from processed CSV file."""
    # Read the CSV file
    logger.info(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Filter out rows without bloomberg_symbol
    df_valid = df[df['bloomberg_symbol'].notna()].copy()
    logger.info(f"Found {len(df_valid)} rows with valid Bloomberg symbols")
    
    cursor = conn.cursor()
    
    # Update each symbol
    updates = 0
    for _, row in df_valid.iterrows():
        symbol = row['bloomberg_symbol']
        bid = row['bid'] if pd.notna(row['bid']) else None
        ask = row['ask'] if pd.notna(row['ask']) else None
        
        if bid is not None or ask is not None:
            cursor.execute("""
                UPDATE FULLPNL 
                SET bid = ?, ask = ?
                WHERE symbol = ?
            """, (bid, ask, symbol))
            
            if cursor.rowcount > 0:
                updates += cursor.rowcount
                logger.debug(f"Updated {symbol}: bid={bid}, ask={ask}")
    
    conn.commit()
    logger.info(f"Updated {updates} rows with bid/ask data")
    return updates


def update_bid_ask_from_database(conn, spot_risk_db_path):
    """Update bid/ask values from spot_risk database (alternative method)."""
    # Attach spot_risk database
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{spot_risk_db_path}' AS spot_risk")
    
    try:
        # Get the latest session
        cursor.execute("""
            SELECT session_id 
            FROM spot_risk.spot_risk_sessions 
            ORDER BY session_id DESC 
            LIMIT 1
        """)
        latest_session = cursor.fetchone()
        
        if not latest_session:
            logger.warning("No sessions found in spot_risk database")
            return 0
        
        session_id = latest_session[0]
        logger.info(f"Using spot_risk session_id: {session_id}")
        
        # Update using JSON extraction
        cursor.execute("""
            UPDATE FULLPNL
            SET 
                bid = CASE 
                    WHEN json_extract(sr.raw_data, '$.bid') = 'nan' THEN NULL
                    ELSE CAST(json_extract(sr.raw_data, '$.bid') AS REAL)
                END,
                ask = CASE 
                    WHEN json_extract(sr.raw_data, '$.ask') = 'nan' THEN NULL
                    ELSE CAST(json_extract(sr.raw_data, '$.ask') AS REAL)
                END
            FROM (
                SELECT bloomberg_symbol, raw_data
                FROM spot_risk.spot_risk_raw
                WHERE session_id = ? AND bloomberg_symbol IS NOT NULL
            ) sr
            WHERE FULLPNL.symbol = sr.bloomberg_symbol
        """, (session_id,))
        
        updates = cursor.rowcount
        conn.commit()
        logger.info(f"Updated {updates} rows from database")
        return updates
        
    finally:
        cursor.execute("DETACH DATABASE spot_risk")


def display_results(conn):
    """Display the updated FULLPNL table."""
    cursor = conn.cursor()
    
    print("\nUpdated FULLPNL Table:")
    print("=" * 80)
    print(f"{'Symbol':<30} {'Bid':>10} {'Ask':>10} {'Spread':>10}")
    print("-" * 80)
    
    cursor.execute("""
        SELECT symbol, bid, ask, 
               CASE WHEN bid IS NOT NULL AND ask IS NOT NULL 
                    THEN ask - bid 
                    ELSE NULL 
               END as spread
        FROM FULLPNL 
        ORDER BY symbol
    """)
    
    for row in cursor.fetchall():
        symbol, bid, ask, spread = row
        bid_str = f"{bid:.6f}" if bid is not None else "NULL"
        ask_str = f"{ask:.6f}" if ask is not None else "NULL"
        spread_str = f"{spread:.6f}" if spread is not None else "NULL"
        print(f"{symbol:<30} {bid_str:>10} {ask_str:>10} {spread_str:>10}")
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(bid) as with_bid,
            COUNT(ask) as with_ask,
            COUNT(CASE WHEN bid IS NOT NULL AND ask IS NOT NULL THEN 1 END) as with_both
        FROM FULLPNL
    """)
    
    total, with_bid, with_ask, with_both = cursor.fetchone()
    print("\nSummary:")
    print(f"  Total symbols: {total}")
    print(f"  With bid data: {with_bid} ({with_bid/total*100:.1f}%)")
    print(f"  With ask data: {with_ask} ({with_ask/total*100:.1f}%)")
    print(f"  With both: {with_both} ({with_both/total*100:.1f}%)")


def main():
    """Main function to add bid/ask to FULLPNL."""
    paths = get_database_paths()
    
    # Connect to pnl_tracker database
    if not os.path.exists(paths['pnl_tracker']):
        logger.error(f"Database not found: {paths['pnl_tracker']}")
        return
    
    conn = sqlite3.connect(paths['pnl_tracker'])
    
    try:
        # Add columns if needed
        add_bid_ask_columns(conn)
        
        # Try to find the latest processed CSV file
        csv_files = []
        if os.path.exists(paths['spot_risk_csv_dir']):
            csv_files = [f for f in os.listdir(paths['spot_risk_csv_dir']) 
                        if f.startswith('bav_analysis_processed_') and f.endswith('.csv')]
        
        if csv_files:
            # Use the most recent CSV file
            latest_csv = sorted(csv_files)[-1]
            csv_path = os.path.join(paths['spot_risk_csv_dir'], latest_csv)
            logger.info(f"Using CSV file: {latest_csv}")
            updates = update_bid_ask_from_csv(conn, csv_path)
        else:
            # Fall back to database method
            logger.info("No CSV files found, using database method")
            if os.path.exists(paths['spot_risk']):
                updates = update_bid_ask_from_database(conn, paths['spot_risk'])
            else:
                logger.error("Neither CSV files nor spot_risk database found")
                return
        
        # Display results
        display_results(conn)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("Adding bid and ask columns to FULLPNL")
    print("=" * 60)
    main() 