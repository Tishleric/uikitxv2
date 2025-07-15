#!/usr/bin/env python
"""Fix EOD Trade Counts

This script updates the trades_count field in the eod_pnl table to reflect
the actual number of trades per instrument per day.
"""

import logging
import sys
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.storage import PnLStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_trade_counts():
    """Fix trade counts in EOD P&L table."""
    storage = PnLStorage()
    
    # Get connection
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Get all EOD records
    cursor.execute("SELECT DISTINCT trade_date, instrument_name FROM eod_pnl")
    eod_records = cursor.fetchall()
    
    logger.info(f"Found {len(eod_records)} EOD records to update")
    
    updates = []
    for record in eod_records:
        trade_date = record['trade_date']
        instrument = record['instrument_name']
        
        # Get actual trade count
        cursor.execute("""
            SELECT COUNT(*) as trade_count 
            FROM processed_trades 
            WHERE instrument_name = ? AND trade_date = ?
        """, (instrument, trade_date))
        
        result = cursor.fetchone()
        actual_count = result['trade_count'] if result else 0
        
        updates.append((actual_count, trade_date, instrument))
        
    # Update all records
    update_query = """
    UPDATE eod_pnl 
    SET trades_count = ?
    WHERE trade_date = ? AND instrument_name = ?
    """
    
    cursor.executemany(update_query, updates)
    conn.commit()
    
    logger.info(f"Updated {len(updates)} EOD records with correct trade counts")
    
    # Show summary
    cursor.execute("""
        SELECT 
            trade_date,
            SUM(trades_count) as total_trades,
            COUNT(DISTINCT instrument_name) as instruments,
            SUM(realized_pnl) as realized,
            SUM(unrealized_pnl) as unrealized,
            SUM(realized_pnl + unrealized_pnl) as total
        FROM eod_pnl
        GROUP BY trade_date
        ORDER BY trade_date DESC
    """)
    
    print("\nUpdated Daily Summary:")
    print("-" * 80)
    print(f"{'Date':<12} {'Trades':<10} {'Instruments':<12} {'Realized P&L':>12} {'Unrealized P&L':>14} {'Total P&L':>12}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        print(f"{row['trade_date']:<12} {row['total_trades']:<10} {row['instruments']:<12} "
              f"{row['realized']:>12.2f} {row['unrealized']:>14.2f} {row['total']:>12.2f}")
    
    conn.close()


if __name__ == "__main__":
    fix_trade_counts() 