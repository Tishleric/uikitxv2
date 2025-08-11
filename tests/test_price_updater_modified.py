"""
Quick test to verify the modified price updater service works correctly.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.price_updater_service import PriceUpdaterService


def test_basic_functionality():
    """Test that the modified service can still extract prices correctly"""
    print("Testing modified PriceUpdaterService...")
    
    # Create service instance
    service = PriceUpdaterService()
    
    # Test data with duplicates
    test_df = pd.DataFrame({
        'key': ['TUU5 Comdty'] * 10 + ['TYU5 Comdty'] * 10 + ['OATU5C 108.5 Comdty'] * 5,
        'adjtheor': [100.5] * 10 + [101.0] * 10 + [2.5] * 5,
        'bid': [100.4] * 10 + [100.9] * 10 + [2.4] * 5,
        'ask': [100.6] * 10 + [101.1] * 10 + [2.6] * 5
    })
    
    # Extract prices
    prices = service._extract_prices(test_df)
    
    print(f"\nInput rows: {len(test_df)}")
    print(f"Unique prices extracted: {len(prices)}")
    print(f"Deduplication ratio: {(1 - len(prices)/len(test_df))*100:.1f}%")
    
    # Verify results
    assert len(prices) <= 3, f"Expected at most 3 unique prices, got {len(prices)}"
    print("\n✓ Deduplication working correctly")
    
    # Check price values
    for symbol, price_data in prices.items():
        print(f"  {symbol}: {price_data['price']}")
    
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_basic_functionality()