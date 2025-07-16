#!/usr/bin/env python3
"""Integration test for price file watcher."""

import time
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.price_watcher import PriceFileWatcher
from lib.trading.pnl_calculator.price_processor import PriceProcessor
from lib.trading.pnl_calculator.storage import PnLStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_price_file(directory: Path, timestamp: str, prices: dict):
    """Create a mock price CSV file."""
    # Create DataFrame with prices
    df = pd.DataFrame({
        'Ticker': list(prices.keys()),
        'PX_LAST': list(prices.values()),
        'PX_SETTLE': [p + 0.05 for p in prices.values()]  # Slightly different settle prices
    })
    
    # Save to CSV
    filename = f"market_prices_{timestamp}.csv"
    file_path = directory / filename
    df.to_csv(file_path, index=False)
    
    logger.info(f"Created mock price file: {file_path}")
    return file_path


def test_price_watcher():
    """Test the price watcher with mock files."""
    # Create test directories
    test_dir = Path("data/test/price_watcher")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = test_dir / "test_prices.db"
    
    storage = None
    watcher = None
    
    try:
        # Initialize components
        storage = PnLStorage(str(db_path))
        processor = PriceProcessor(storage)
        
        # Create processor callback
        def process_callback(file_path: Path):
            logger.info(f"Processing file: {file_path}")
            prices = processor.process_price_file(file_path)
            logger.info(f"Extracted {len(prices)} prices")
        
        # Create watcher
        watcher = PriceFileWatcher([str(test_dir)], process_callback)
        
        # Test 1: Process existing files
        logger.info("\n=== Test 1: Processing existing files ===")
        
        # Create files in different time windows
        chicago_tz = pytz.timezone('America/Chicago')
        now = datetime.now(chicago_tz)
        
        # 2pm window file
        create_mock_price_file(test_dir, f"{now.strftime('%Y%m%d')}_1400", {
            'TY': 110.25,
            'TU': 105.50,
            'FV': 108.75,
            'US': 125.00,
            'WN': 122.50
        })
        
        # 4pm window file  
        create_mock_price_file(test_dir, f"{now.strftime('%Y%m%d')}_1600", {
            'TY': 110.50,
            'TU': 105.75,
            'FV': 109.00,
            'US': 125.25,
            'WN': 122.75
        })
        
        # 3pm file (should be ignored)
        create_mock_price_file(test_dir, f"{now.strftime('%Y%m%d')}_1500", {
            'TY': 110.35,
            'TU': 105.60,
            'FV': 108.85,
            'US': 125.10,
            'WN': 122.60
        })
        
        # Start watcher
        logger.info("Starting price file watcher...")
        watcher.start()
        
        # Wait for processing
        time.sleep(2)
        
        # Check stored prices
        latest_prices = processor.get_latest_prices()
        logger.info(f"Latest prices in database: {latest_prices}")
        
        # Test 2: Real-time file detection
        logger.info("\n=== Test 2: Real-time file detection ===")
        
        # Create a new file while watcher is running
        new_file = create_mock_price_file(test_dir, f"{now.strftime('%Y%m%d')}_1415", {
            'TY': 110.60,
            'TU': 105.85,
            'FV': 109.10,
            'US': 125.35,
            'WN': 122.85
        })
        
        # Wait for detection and processing
        time.sleep(2)
        
        # Check updated prices
        updated_prices = processor.get_latest_prices()
        logger.info(f"Updated prices after new file: {updated_prices}")
        
        # Verify we still have prices (4pm file is still the latest)
        assert 'TY' in updated_prices
        assert updated_prices['TY'] == 110.55, f"Expected TY=110.55 (from 4pm file), got {updated_prices['TY']}"
        
        # Test 3: Check price history
        logger.info("\n=== Test 3: Price history ===")
        
        # Get TY price at different times  
        # Note: 2:15pm file should be selected for 2pm window
        ty_price_215pm = processor.get_price_at_time('TY', chicago_tz.localize(
            datetime(now.year, now.month, now.day, 14, 15)
        ))
        ty_price_4pm = processor.get_price_at_time('TY', chicago_tz.localize(
            datetime(now.year, now.month, now.day, 16, 0)
        ))
        
        logger.info(f"TY price at 2:15pm: {ty_price_215pm}")
        logger.info(f"TY price at 4pm: {ty_price_4pm}")
        
        assert ty_price_215pm == 110.60, f"Expected TY=110.60 at 2:15pm, got {ty_price_215pm}"
        assert ty_price_4pm == 110.55, f"Expected TY=110.55 at 4pm, got {ty_price_4pm}"
        
        logger.info("\n✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise
    finally:
        # Stop watcher first
        if watcher and watcher.is_running:
            logger.info("\nStopping price file watcher...")
            watcher.stop()
            time.sleep(1)  # Give it time to fully stop
        
        # Cleanup
        import shutil
        if test_dir.exists():
            try:
                shutil.rmtree(test_dir)
                logger.info("Cleaned up test directory")
            except Exception as e:
                logger.warning(f"Could not fully clean up test directory: {e}")


if __name__ == "__main__":
    test_price_watcher() 