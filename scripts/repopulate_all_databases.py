#!/usr/bin/env python
"""
Repopulate all databases with latest schema and reprocess all data.

This script:
1. Backs up existing databases
2. Recreates all tables with latest schema
3. Reprocesses all source data
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.trade_file_watcher import TradeFileWatcher
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.market_prices.storage import MarketPriceStorage
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService
from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database(db_path: Path) -> Path:
    """Create a backup of the database."""
    if not db_path.exists():
        logger.info(f"No existing database to backup: {db_path}")
        return None
        
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    
    shutil.copy2(db_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path


def repopulate_pnl_database():
    """Recreate and repopulate the P&L tracking database."""
    logger.info("\n=== Repopulating P&L Database ===")
    
    db_path = Path("data/output/pnl/pnl_tracker.db")
    
    # Backup existing database
    backup_database(db_path)
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Removed existing database: {db_path}")
    
    # Create new storage instance (will create fresh database)
    storage = PnLStorage(str(db_path))
    logger.info("Created new P&L database with latest schema")
    
    # Process all trade files
    trade_dir = Path("data/input/trade_ledger")
    if trade_dir.exists():
        logger.info(f"Processing trade files from {trade_dir}")
        
        # Use file watcher to process all existing files
        watcher = TradeFileWatcher(
            input_dir=str(trade_dir),
            output_dir="data/output/trade_ledger_processed"
        )
        
        # Process existing files
        csv_files = sorted(trade_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} trade files to process")
        
        # Initialize position manager for position tracking
        position_manager = PositionManager(storage)
        
        for csv_file in csv_files:
            logger.info(f"Processing {csv_file.name}")
            try:
                # Process the trade file and get processed trades
                processed_trades = watcher.preprocessor.process_trade_file(str(csv_file))
                
                # Create positions from trades if any were returned
                if processed_trades and isinstance(processed_trades, list):
                    logger.info(f"Creating positions from {len(processed_trades)} trades")
                    for trade in processed_trades:
                        # Only process valid trades (not SOD or exercised)
                        if not trade.get('is_sod', False) and not trade.get('is_exercise', False):
                            try:
                                position_update = position_manager.process_trade(trade)
                                logger.debug(f"Position update for {trade['instrumentName']}: {position_update.trade_action}")
                            except Exception as e:
                                logger.warning(f"Could not process trade {trade.get('tradeId')}: {e}")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file.name}: {e}")
    else:
        logger.warning(f"Trade directory not found: {trade_dir}")
    
    logger.info("P&L database repopulation complete")


def repopulate_market_prices_database():
    """Recreate and repopulate the market prices database."""
    logger.info("\n=== Repopulating Market Prices Database ===")
    
    db_path = Path("data/output/market_prices/market_prices.db")
    
    # Backup existing database
    backup_database(db_path)
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Removed existing database: {db_path}")
    
    # Create new storage instance
    storage = MarketPriceStorage(str(db_path))
    logger.info("Created new market prices database with latest schema")
    
    # Note: Market price processing would need to be implemented
    # For now, just create the empty database with schema
    logger.info("Market prices database ready for data")


def repopulate_spot_risk_database():
    """Recreate and repopulate the spot risk database."""
    logger.info("\n=== Repopulating Spot Risk Database ===")
    
    db_path = Path("data/output/spot_risk/spot_risk.db")
    
    # Backup existing database
    backup_database(db_path)
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Removed existing database: {db_path}")
    
    # Create new database service
    db_service = SpotRiskDatabaseService(db_path)
    logger.info("Created new spot risk database with latest schema")
    
    # Update existing Bloomberg symbols
    logger.info("Updating Bloomberg symbols for existing data...")
    try:
        # Run migration to populate Bloomberg symbols
        from scripts.update_spot_risk_bloomberg_symbols import update_bloomberg_symbols
        update_bloomberg_symbols(str(db_path))
    except Exception as e:
        logger.warning(f"Could not update Bloomberg symbols: {e}")
    
    # Process spot risk files
    spot_risk_dir = Path("data/input/actant_spot_risk")
    output_dir = Path("data/output/spot_risk/processed")
    
    if spot_risk_dir.exists():
        logger.info(f"Processing spot risk files from {spot_risk_dir}")
        
        # Use file watcher to process all existing files
        watcher = SpotRiskWatcher(
            input_dir=str(spot_risk_dir),
            output_dir=str(output_dir)
        )
        
        # Process existing files
        watcher._process_existing_files()
        
        logger.info("Spot risk processing complete")
    else:
        logger.warning(f"Spot risk directory not found: {spot_risk_dir}")


def main():
    """Main execution function."""
    logger.info("Starting database repopulation process...")
    
    # Repopulate all databases
    repopulate_pnl_database()
    repopulate_market_prices_database()
    repopulate_spot_risk_database()
    
    logger.info("\n=== Database Repopulation Complete ===")
    logger.info("All databases have been recreated with latest schema")
    logger.info("Source data has been reprocessed where available")
    

if __name__ == "__main__":
    main() 