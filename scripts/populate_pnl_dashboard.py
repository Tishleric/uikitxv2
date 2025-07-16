#!/usr/bin/env python
"""Populate the P&L dashboard database with existing test data."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_calculator.trade_preprocessor import TradePreprocessor
from lib.trading.pnl_calculator.price_processor import PriceProcessor
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_existing_files():
    """Process existing trade and price files into the database."""
    
    # Initialize service
    db_path = "data/output/pnl/pnl_dashboard.db"
    trade_ledger_dir = "data/input/trade_ledger"
    price_directories = [
        "data/input/market_prices/futures",
        "data/input/market_prices/options"
    ]
    
    logger.info(f"Initializing P&L service with database: {db_path}")
    
    service = UnifiedPnLService(
        db_path=db_path,
        trade_ledger_dir=trade_ledger_dir,
        price_directories=price_directories
    )
    
    # Process trade files manually
    trade_dir = Path(trade_ledger_dir)
    trade_files = list(trade_dir.glob("*.csv"))
    logger.info(f"Found {len(trade_files)} trade files to process")
    
    for trade_file in trade_files:
        logger.info(f"Processing trade file: {trade_file}")
        try:
            # Use the service's trade preprocessor
            service.trade_preprocessor.process_trade_file(str(trade_file))
            logger.info(f"Successfully processed {trade_file}")
        except Exception as e:
            logger.error(f"Error processing {trade_file}: {e}")
    
    # Process price files manually
    for price_dir in price_directories:
        price_path = Path(price_dir)
        price_files = list(price_path.glob("*.csv"))
        logger.info(f"Found {len(price_files)} price files in {price_dir}")
        
        for price_file in price_files:
            logger.info(f"Processing price file: {price_file}")
            try:
                # Use the service's price processor - pass Path object, not string
                service.price_processor.process_price_file(price_file)
                logger.info(f"Successfully processed {price_file}")
            except Exception as e:
                logger.error(f"Error processing {price_file}: {e}")
    
    # Get summary of what was loaded
    logger.info("\n=== Database Summary ===")
    
    # Check positions
    positions = service.get_open_positions()
    logger.info(f"Open positions: {len(positions)}")
    for pos in positions[:5]:  # Show first 5
        logger.info(f"  {pos.get('symbol')}: {pos.get('quantity')} @ avg ${pos.get('avg_price', 0):.4f}")
    
    # Check trades
    trades = service.get_trade_history(limit=5)
    logger.info(f"\nRecent trades: {len(trades)} shown")
    for trade in trades:
        logger.info(f"  {trade.get('trade_time')}: {trade.get('action')} {trade.get('quantity')} {trade.get('symbol')} @ ${trade.get('price', 0):.4f}")
    
    # Check daily P&L
    daily_pnl = service.get_daily_pnl_history()
    logger.info(f"\nDaily P&L history: {len(daily_pnl)} days")
    for day in daily_pnl[:5]:  # Show first 5
        logger.info(f"  {day.get('snapshot_date')}: Realized ${day.get('realized_pnl', 0):.2f}, Unrealized ${day.get('unrealized_pnl', 0):.2f}")
    
    logger.info("\nDatabase population complete!")

if __name__ == "__main__":
    process_existing_files() 