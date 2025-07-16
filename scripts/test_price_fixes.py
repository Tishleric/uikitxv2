#!/usr/bin/env python
"""Test the price-related fixes we just made."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager
from lib.trading.pnl_calculator.price_processor import PriceProcessor
from datetime import datetime
import pytz

def test_fixes():
    """Test that our fixes work correctly."""
    
    print("Testing price fixes...")
    
    # Test 1: Position Manager now uses storage.get_market_price
    print("\n1. Testing PositionManager.update_market_prices()...")
    try:
        storage = PnLStorage("data/output/pnl/pnl_tracker.db")
        position_manager = PositionManager(storage)
        
        # This should no longer throw 'PriceFileSelector has no attribute get_market_price'
        position_manager.update_market_prices()
        print("   ✓ PositionManager.update_market_prices() works correctly")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: PriceProcessor handles both string and Path
    print("\n2. Testing PriceProcessor with string path...")
    try:
        processor = PriceProcessor(storage)
        
        # Test with string (should be converted to Path internally)
        test_file = "data/input/market_prices/futures/Futures_20250714_1600.csv"
        if Path(test_file).exists():
            result = processor.process_price_file(test_file)
            print(f"   ✓ Processed {len(result)} prices from string path")
        else:
            print(f"   - Test file not found: {test_file}")
            
        # Test with Path object
        test_path = Path("data/input/market_prices/futures/Futures_20250714_1600.csv")
        if test_path.exists():
            result = processor.process_price_file(test_path)
            print(f"   ✓ Processed {len(result)} prices from Path object")
        else:
            print(f"   - Test file not found: {test_path}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_fixes() 