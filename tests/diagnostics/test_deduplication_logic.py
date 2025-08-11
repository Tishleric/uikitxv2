"""
Test Deduplication Logic
========================
Unit tests for the deduplication functionality.
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.diagnostics.price_updater_service_optimized import PriceUpdaterServiceOptimized


def test_deduplication():
    """Test various deduplication scenarios"""
    
    # Create test instance
    updater = PriceUpdaterServiceOptimized("dummy.db")
    
    print("Testing Deduplication Logic")
    print("="*50)
    
    # Test 1: Duplicate futures
    print("\nTest 1: Duplicate futures (typical scenario)")
    df1 = pd.DataFrame({
        'key': ['XCME.ZN.SEP25'] * 17 + ['XCME.ZT.SEP25'] * 17,
        'adjtheor': [100.5] * 17 + [95.25] * 17,
        'bid': [100.4] * 17 + [95.20] * 17,
        'ask': [100.6] * 17 + [95.30] * 17
    })
    
    # Mock the symbol translator
    class MockTranslator:
        def translate(self, symbol, from_fmt, to_fmt):
            mapping = {
                'XCME.ZN.SEP25': 'TYU5 Comdty',
                'XCME.ZT.SEP25': 'TUU5 Comdty',
                'XCME.WY1.06AUG25.110.C': 'TYWQ25C1 110 Comdty'
            }
            return mapping.get(symbol)
    
    updater.symbol_translator = MockTranslator()
    
    prices = updater._extract_prices_deduplicated(df1)
    print(f"  Input rows: {len(df1)}")
    print(f"  Unique prices: {len(prices)}")
    print(f"  Deduplication ratio: {(1 - len(prices)/len(df1))*100:.1f}%")
    assert len(prices) == 2, f"Expected 2 unique prices, got {len(prices)}"
    print("  ✓ Pass")
    
    # Test 2: No duplicates
    print("\nTest 2: No duplicates (all unique)")
    df2 = pd.DataFrame({
        'key': ['XCME.ZN.SEP25', 'XCME.ZT.SEP25', 'XCME.WY1.06AUG25.110.C'],
        'adjtheor': [100.5, 95.25, 2.125],
        'bid': [100.4, 95.20, 2.100],
        'ask': [100.6, 95.30, 2.150]
    })
    
    prices = updater._extract_prices_deduplicated(df2)
    print(f"  Input rows: {len(df2)}")
    print(f"  Unique prices: {len(prices)}")
    assert len(prices) == 3, f"Expected 3 unique prices, got {len(prices)}"
    print("  ✓ Pass")
    
    # Test 3: Price changes for same symbol
    print("\nTest 3: Price changes for same symbol (keep last)")
    df3 = pd.DataFrame({
        'key': ['XCME.ZN.SEP25', 'XCME.ZN.SEP25', 'XCME.ZN.SEP25'],
        'adjtheor': [100.5, 100.6, 100.7],  # Price increases
        'bid': [100.4, 100.5, 100.6],
        'ask': [100.6, 100.7, 100.8]
    })
    
    prices = updater._extract_prices_deduplicated(df3)
    print(f"  Input rows: {len(df3)}")
    print(f"  Unique prices: {len(prices)}")
    assert len(prices) == 1, f"Expected 1 unique price, got {len(prices)}"
    assert prices['TYU5 Comdty']['price'] == 100.7, "Should keep last price"
    print(f"  Final price: {prices['TYU5 Comdty']['price']}")
    print("  ✓ Pass - keeps last occurrence")
    
    # Test 4: Missing prices
    print("\nTest 4: Missing prices (NaN handling)")
    df4 = pd.DataFrame({
        'key': ['XCME.ZN.SEP25', 'XCME.ZT.SEP25', 'XCME.ZN.SEP25'],
        'adjtheor': [100.5, None, 100.6],  # Middle one missing
        'bid': [100.4, 95.20, 100.5],
        'ask': [100.6, 95.30, 100.7]
    })
    
    prices = updater._extract_prices_deduplicated(df4)
    print(f"  Input rows: {len(df4)}")
    print(f"  Unique prices: {len(prices)}")
    # ZT should use bid/ask midpoint, ZN should have last value
    assert len(prices) == 2, f"Expected 2 unique prices, got {len(prices)}"
    assert prices['TUU5 Comdty']['price'] == 95.25, "Should use bid/ask midpoint"
    print("  ✓ Pass - handles missing adjtheor")
    
    # Test 5: Real-world scenario
    print("\nTest 5: Real-world scenario (mixed futures and options)")
    df5 = pd.DataFrame({
        'key': (['XCME.ZN.SEP25'] * 17 + 
                ['XCME.ZT.SEP25'] * 17 + 
                ['XCME.WY1.06AUG25.110.C'] * 5),
        'adjtheor': ([100.5] * 17 + [95.25] * 17 + [2.125] * 5),
        'bid': ([100.4] * 17 + [95.20] * 17 + [2.100] * 5),
        'ask': ([100.6] * 17 + [95.30] * 17 + [2.150] * 5)
    })
    
    prices = updater._extract_prices_deduplicated(df5)
    print(f"  Input rows: {len(df5)} (17+17+5)")
    print(f"  Unique prices: {len(prices)}")
    print(f"  Deduplication ratio: {(1 - len(prices)/len(df5))*100:.1f}%")
    assert len(prices) == 3, f"Expected 3 unique prices, got {len(prices)}"
    print("  ✓ Pass - typical spot risk batch")
    
    print("\n" + "="*50)
    print("All deduplication tests passed! ✓")


if __name__ == "__main__":
    test_deduplication()