#!/usr/bin/env python3
"""Simple test for price processor."""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.price_processor import PriceProcessor


def test_price_processor():
    """Test the price processor directly."""
    # Create test database
    db_path = "data/test/price_processor_test.db"
    Path("data/test").mkdir(parents=True, exist_ok=True)
    
    # Initialize storage and processor
    storage = PnLStorage(db_path)
    processor = PriceProcessor(storage)
    
    # Create a test price file
    chicago_tz = pytz.timezone('America/Chicago')
    now = datetime.now(chicago_tz)
    
    test_file = Path("data/test/market_prices_20250715_1400.csv")
    df = pd.DataFrame({
        'Ticker': ['TY', 'TU', 'FV', 'US', 'WN'],
        'PX_LAST': [110.25, 105.50, 108.75, 125.00, 122.50],
        'PX_SETTLE': [110.30, 105.55, 108.80, 125.05, 122.55]
    })
    df.to_csv(test_file, index=False)
    
    print(f"Created test file: {test_file}")
    
    # Process the file
    prices = processor.process_price_file(test_file)
    print(f"Processed prices: {prices}")
    
    # Get latest prices
    latest = processor.get_latest_prices()
    print(f"Latest prices from DB: {latest}")
    
    # Cleanup
    test_file.unlink()
    Path(db_path).unlink()
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_price_processor() 