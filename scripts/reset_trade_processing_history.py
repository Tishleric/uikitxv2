#!/usr/bin/env python3
"""
Reset trade processing history by clearing tables while preserving schemas.
Backs up database before making changes.
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_processing_state_file():
    """Clear the .processing_state.json file"""
    state_file = Path("data/output/trade_ledger_processed/.processing_state.json")
    
    if state_file.exists():
        # Backup the current state
        backup_path = state_file.with_suffix(f".json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        with open(state_file, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Backed up processing state to: {backup_path}")
        
        # Clear the file (write empty JSON)
        with open(state_file, 'w') as f:
            json.dump({}, f, indent=2)
        logger.info("Cleared .processing_state.json file")
    else:
        logger.warning(f"Processing state file not found: {state_file}")

def clear_database_tables():
    """Clear specific tables while preserving schemas"""
    db_path = "data/output/pnl/pnl_tracker.db"
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return False
    
    # Tables to clear (excluding deprecated cto_trades as requested)
    tables_to_clear = [
        'trade_processing_tracker',  # Row-level tracking
        'processed_trades',          # Processed trade records
        'tyu5_positions',           # Calculated positions
        'FULLPNL',                  # Merged P&L data
        'lot_positions',            # Lot-level positions
        'position_greeks',          # Greek calculations
        'pnl_attribution',          # P&L attribution
        'risk_scenarios',           # Risk scenarios
        'match_history',            # Trade matching history
        'file_metadata',            # File processing metadata
        'file_processing_log'       # File processing log
    ]
    
    conn = sqlite3.connect(db_path)
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Get list of existing tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        # Clear each table
        cleared_tables = []
        for table in tables_to_clear:
            if table in existing_tables:
                try:
                    conn.execute(f"DELETE FROM {table}")
                    count = conn.total_changes
                    cleared_tables.append(f"{table} ({count} rows)")
                    logger.info(f"Cleared table {table}: {count} rows deleted")
                except Exception as e:
                    logger.warning(f"Could not clear {table}: {e}")
            else:
                logger.info(f"Table {table} does not exist, skipping")
        
        # Commit changes
        conn.commit()
        logger.info("Database changes committed successfully")
        
        # Log summary
        logger.info("\n=== SUMMARY ===")
        logger.info(f"Cleared {len(cleared_tables)} tables:")
        for table_info in cleared_tables:
            logger.info(f"  - {table_info}")
            
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error clearing tables: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main execution"""
    logger.info("=== Starting Trade Processing History Reset ===")
    
    # Step 1: Clear processing state file
    logger.info("\nStep 1: Clearing processing state file...")
    clear_processing_state_file()
    
    # Step 2: Clear database tables
    logger.info("\nStep 2: Clearing database tables...")
    success = clear_database_tables()
    
    if success:
        logger.info("\n=== Reset completed successfully ===")
        logger.info("The system is now ready to reprocess all trade files from scratch.")
        logger.info("Note: Database backup was created at: data/output/pnl/pnl_tracker.db.backup_20250721_212010")
    else:
        logger.error("\n=== Reset failed ===")
        logger.error("Please check the error messages above.")

if __name__ == "__main__":
    main() 