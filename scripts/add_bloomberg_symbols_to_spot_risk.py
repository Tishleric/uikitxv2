#!/usr/bin/env python3
"""
Migration script to add bloomberg_symbol column to existing spot risk database
and populate it with translated values.
"""

import sqlite3
import logging
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_spot_risk_db(db_path: str = "data/output/spot_risk/spot_risk.db"):
    """Add bloomberg_symbol column and populate with translations."""
    
    db_path = Path(db_path)
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    translator = RosettaStone()
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(spot_risk_raw)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'bloomberg_symbol' not in columns:
            logger.info("Adding bloomberg_symbol column...")
            cursor.execute("""
                ALTER TABLE spot_risk_raw 
                ADD COLUMN bloomberg_symbol TEXT
            """)
            
            # Add index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_bloomberg 
                ON spot_risk_raw(bloomberg_symbol)
            """)
            conn.commit()
            logger.info("Column and index added successfully")
        else:
            logger.info("bloomberg_symbol column already exists")
        
        # Update existing rows with Bloomberg symbols
        logger.info("Translating existing instrument keys...")
        
        cursor.execute("""
            SELECT id, instrument_key 
            FROM spot_risk_raw 
            WHERE bloomberg_symbol IS NULL
        """)
        
        rows_to_update = cursor.fetchall()
        logger.info(f"Found {len(rows_to_update)} rows to translate")
        
        translated_count = 0
        failed_count = 0
        
        for row_id, instrument_key in rows_to_update:
            if not instrument_key:
                continue
                
            try:
                bloomberg_symbol = translator.translate(instrument_key, 'actantrisk', 'bloomberg')
                if bloomberg_symbol:
                    cursor.execute("""
                        UPDATE spot_risk_raw 
                        SET bloomberg_symbol = ? 
                        WHERE id = ?
                    """, (bloomberg_symbol, row_id))
                    translated_count += 1
                    
                    if translated_count % 100 == 0:
                        logger.info(f"Translated {translated_count} symbols...")
                else:
                    failed_count += 1
                    logger.debug(f"No translation for: {instrument_key}")
                    
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to translate {instrument_key}: {e}")
        
        # Recreate the view to include bloomberg_symbol
        logger.info("Recreating latest_calculations view...")
        cursor.execute("DROP VIEW IF EXISTS latest_calculations")
        cursor.execute("""
            CREATE VIEW latest_calculations AS
            SELECT 
                r.instrument_key,
                r.bloomberg_symbol,
                r.instrument_type,
                r.expiry_date,
                r.strike,
                r.midpoint_price,
                c.*
            FROM spot_risk_raw r
            INNER JOIN spot_risk_calculated c ON r.id = c.raw_id
            WHERE c.id IN (
                SELECT MAX(c2.id)
                FROM spot_risk_calculated c2
                GROUP BY c2.raw_id
            )
        """)
        
        conn.commit()
        logger.info(f"Migration complete: {translated_count} symbols translated, {failed_count} failed")
        
        # Show sample of translations
        cursor.execute("""
            SELECT instrument_key, bloomberg_symbol 
            FROM spot_risk_raw 
            WHERE bloomberg_symbol IS NOT NULL 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        if samples:
            logger.info("Sample translations:")
            for actant, bloomberg in samples:
                logger.info(f"  {actant} → {bloomberg}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = migrate_spot_risk_db()
    sys.exit(0 if success else 1) 