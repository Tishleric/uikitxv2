#!/usr/bin/env python3
"""
Test script to verify Bloomberg symbol translation in spot risk processing.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_bloomberg_translation():
    """Test Bloomberg symbol translation in spot risk pipeline."""
    
    # Find a test file
    test_file = Path("data/input/actant_spot_risk/bav_analysis_20250711_105540.csv")
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False
    
    logger.info(f"Processing test file: {test_file}")
    
    # Parse the CSV
    df = parse_spot_risk_csv(test_file)
    logger.info(f"Parsed {len(df)} rows")
    
    # Check if bloomberg_symbol column exists
    if 'bloomberg_symbol' not in df.columns:
        logger.error("bloomberg_symbol column not found in parsed DataFrame!")
        return False
    
    # Show sample of translations
    logger.info("\nSample Bloomberg translations from parser:")
    sample_df = df[df['bloomberg_symbol'].notna()].head(10)
    
    if not sample_df.empty:
        for idx, row in sample_df.iterrows():
            key = row.get('key', row.get('instrument_key', 'N/A'))
            bloomberg = row['bloomberg_symbol']
            logger.info(f"  {key} → {bloomberg}")
    else:
        logger.warning("No Bloomberg translations found in parsed data")
    
    # Test database storage
    db_service = SpotRiskDatabaseService()
    
    # Create a test session
    session_id = db_service.create_session(
        source_file=str(test_file),
        data_timestamp="20250711_105540"
    )
    
    # Insert raw data
    rows_inserted = db_service.insert_raw_data(df, session_id)
    logger.info(f"\nInserted {rows_inserted} rows into database")
    
    # Query database to verify Bloomberg symbols were stored
    conn = sqlite3.connect(str(db_service.db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT instrument_key, bloomberg_symbol, instrument_type
        FROM spot_risk_raw
        WHERE session_id = ?
        AND bloomberg_symbol IS NOT NULL
        LIMIT 10
    """, (session_id,))
    
    db_results = cursor.fetchall()
    
    if db_results:
        logger.info("\nBloomberg symbols in database:")
        for actant, bloomberg, itype in db_results:
            logger.info(f"  {itype}: {actant} → {bloomberg}")
    else:
        logger.warning("No Bloomberg symbols found in database")
    
    # Check for any untranslated symbols
    cursor.execute("""
        SELECT COUNT(*) 
        FROM spot_risk_raw
        WHERE session_id = ?
        AND bloomberg_symbol IS NULL
    """, (session_id,))
    
    untranslated_count = cursor.fetchone()[0]
    if untranslated_count > 0:
        logger.warning(f"\n{untranslated_count} symbols could not be translated")
        
        # Show sample of untranslated
        cursor.execute("""
            SELECT instrument_key, instrument_type
            FROM spot_risk_raw
            WHERE session_id = ?
            AND bloomberg_symbol IS NULL
            LIMIT 5
        """, (session_id,))
        
        for actant, itype in cursor.fetchall():
            logger.warning(f"  Untranslated {itype}: {actant}")
    
    conn.close()
    
    # Generate CSV output
    calculator = SpotRiskGreekCalculator()
    df_with_greeks, results = calculator.calculate_greeks(df)
    df_with_aggregates = calculator.calculate_aggregates(df_with_greeks)
    
    # Check if bloomberg_symbol is in final output
    if 'bloomberg_symbol' in df_with_aggregates.columns:
        logger.info("\n✓ bloomberg_symbol column present in final CSV output")
        
        # Save a sample output
        output_path = Path("data/output/spot_risk/test_bloomberg_output.csv")
        df_with_aggregates.to_csv(output_path, index=False)
        logger.info(f"Sample output saved to: {output_path}")
    else:
        logger.error("\n✗ bloomberg_symbol column missing from final CSV output!")
        return False
    
    return True


if __name__ == "__main__":
    success = test_bloomberg_translation()
    sys.exit(0 if success else 1) 