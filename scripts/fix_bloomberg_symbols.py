#!/usr/bin/env python
"""Fix Bloomberg symbols that failed translation due to regex pattern issue."""

import sys
from pathlib import Path
import sqlite3
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_bloomberg_symbols():
    """Update Bloomberg symbols for records that failed translation."""
    
    db_path = "data/output/spot_risk/spot_risk.db"
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        return
        
    translator = RosettaStone()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all records without Bloomberg symbols
    cursor.execute("""
        SELECT id, instrument_key 
        FROM spot_risk_raw 
        WHERE bloomberg_symbol IS NULL OR bloomberg_symbol = ''
    """)
    
    records = cursor.fetchall()
    logger.info(f"Found {len(records)} records to fix")
    
    updated = 0
    failed = 0
    
    for record_id, instrument_key in records:
        try:
            bloomberg_symbol = translator.translate(instrument_key, 'actantrisk', 'bloomberg')
            if bloomberg_symbol:
                cursor.execute(
                    "UPDATE spot_risk_raw SET bloomberg_symbol = ? WHERE id = ?",
                    (bloomberg_symbol, record_id)
                )
                updated += 1
                if updated % 100 == 0:
                    logger.info(f"Updated {updated} records...")
            else:
                failed += 1
                if failed <= 5:  # Show first 5 failures
                    logger.warning(f"Failed to translate: {instrument_key}")
        except Exception as e:
            logger.error(f"Error translating {instrument_key}: {e}")
            failed += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Fix complete: {updated} successful, {failed} failed")
    
    # Check results
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM spot_risk_raw WHERE bloomberg_symbol IS NOT NULL")
    total_with_symbols = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM spot_risk_raw")
    total_records = cursor.fetchone()[0]
    conn.close()
    
    logger.info(f"Final status: {total_with_symbols}/{total_records} records have Bloomberg symbols")


if __name__ == "__main__":
    fix_bloomberg_symbols() 