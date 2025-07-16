#!/usr/bin/env python3
"""Example usage of the price file watcher."""

import sys
import logging
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.price_processor import PriceProcessor
from lib.trading.pnl_calculator.price_watcher import PriceFileWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the price watcher example."""
    # Configuration
    price_directories = [
        "data/bloomberg/prices",  # Main price directory
        # Add more directories as needed
    ]
    
    db_path = "data/output/pnl/market_prices.db"
    
    # Ensure directories exist
    for dir_path in price_directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    logger.info("Initializing price monitoring system...")
    storage = PnLStorage(db_path)
    processor = PriceProcessor(storage)
    
    # Create processor callback
    def process_price_file(file_path: Path):
        """Callback to process detected price files."""
        try:
            logger.info(f"Processing new price file: {file_path}")
            prices = processor.process_price_file(file_path)
            logger.info(f"Successfully processed {len(prices)} prices")
            
            # Log a sample of prices
            for symbol in list(prices.keys())[:3]:
                logger.info(f"  {symbol}: ${prices[symbol]}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    # Create and start watcher
    watcher = PriceFileWatcher(price_directories, process_price_file)
    
    try:
        logger.info("Starting price file watcher...")
        logger.info(f"Monitoring directories: {price_directories}")
        logger.info("Press Ctrl+C to stop")
        
        watcher.start()
        
        # Keep running and periodically show latest prices
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            # Get and display latest prices
            latest_prices = processor.get_latest_prices()
            if latest_prices:
                logger.info("Latest market prices:")
                for symbol, price in sorted(latest_prices.items()):
                    logger.info(f"  {symbol}: ${price:.5f}")
            else:
                logger.info("No prices available yet")
                
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        watcher.stop()
        logger.info("Price watcher stopped")


if __name__ == "__main__":
    main() 