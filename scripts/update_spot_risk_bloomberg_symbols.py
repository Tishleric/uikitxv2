#!/usr/bin/env python
"""Update Bloomberg symbols in existing spot risk database."""

import sys
from pathlib import Path
import sqlite3
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_bloomberg_symbols(db_path: str):
    """Update Bloomberg symbols for all records in spot_risk_raw table."""
    
    translator = SpotRiskSymbolTranslator()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all records without Bloomberg symbols
    cursor.execute("""
        SELECT id, instrument_key 
        FROM spot_risk_raw 
        WHERE bloomberg_symbol IS NULL OR bloomberg_symbol = ''
    """)
    
    records = cursor.fetchall()
    logger.info(f"Found {len(records)} records to update")
    
    updated = 0
    failed = 0
    
    for record_id, instrument_key in records:
        try:
            bloomberg_symbol = translator.translate(instrument_key)
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
        except Exception as e:
            logger.error(f"Error translating {instrument_key}: {e}")
            failed += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Update complete: {updated} successful, {failed} failed")
    return updated, failed


if __name__ == "__main__":
    db_path = "data/output/spot_risk/spot_risk.db"
    if Path(db_path).exists():
        update_bloomberg_symbols(db_path)
    else:
        logger.error(f"Database not found: {db_path}") 