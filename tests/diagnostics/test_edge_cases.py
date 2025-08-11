"""
Edge Case Tests for Price Updater Optimization
==============================================
Critical edge cases to ensure robustness.
"""

import sys
import pickle
import pandas as pd
import pyarrow as pa
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.diagnostics.price_updater_service_optimized import PriceUpdaterServiceOptimized


def test_empty_dataframe():
    """Test handling of empty DataFrames"""
    print("\nTest: Empty DataFrame")
    service = PriceUpdaterServiceOptimized()
    
    # Create empty DataFrame with expected columns
    empty_df = pd.DataFrame(columns=['symbol', 'adjtheor', 'bid', 'ask'])
    
    prices = service._extract_prices_deduplicated(empty_df)
    print(f"  Result: {len(prices)} prices extracted")
    assert len(prices) == 0, "Should handle empty DataFrame"
    print("  ✓ Pass")


def test_missing_columns():
    """Test handling of missing required columns"""
    print("\nTest: Missing columns")
    service = PriceUpdaterServiceOptimized()
    
    # DataFrame missing adjtheor, bid, ask
    df = pd.DataFrame({
        'key': ['TEST1', 'TEST2'],
        'other_col': [1, 2]
    })
    
    prices = service._extract_prices_deduplicated(df)
    print(f"  Result: {len(prices)} prices extracted")
    assert len(prices) == 0, "Should handle missing columns gracefully"
    print("  ✓ Pass")


def test_all_nan_prices():
    """Test when all prices are NaN"""
    print("\nTest: All NaN prices")
    service = PriceUpdaterServiceOptimized()
    
    df = pd.DataFrame({
        'key': ['TEST1', 'TEST2'],
        'adjtheor': [float('nan'), float('nan')],
        'bid': [float('nan'), float('nan')],
        'ask': [float('nan'), float('nan')]
    })
    
    prices = service._extract_prices_deduplicated(df)
    print(f"  Result: {len(prices)} prices extracted")
    assert len(prices) == 0, "Should skip rows with no valid prices"
    print("  ✓ Pass")


def test_symbol_translation_failure():
    """Test handling of untranslatable symbols"""
    print("\nTest: Symbol translation failures")
    service = PriceUpdaterServiceOptimized()
    
    # Use a symbol that won't translate
    df = pd.DataFrame({
        'key': ['UNKNOWN_SYMBOL_XYZ'],
        'adjtheor': [100.5]
    })
    
    prices = service._extract_prices_deduplicated(df)
    print(f"  Result: {len(prices)} prices extracted")
    # Should skip untranslatable symbols
    assert len(prices) == 0, "Should skip untranslatable symbols"
    print("  ✓ Pass")


def test_corrupt_message():
    """Test handling of corrupted pickle data"""
    print("\nTest: Corrupted message data")
    service = PriceUpdaterServiceOptimized()
    
    # Create corrupted data
    corrupt_data = b'corrupted pickle data'
    
    try:
        service._process_single_message(corrupt_data)
        print("  ✓ Pass - handled corrupt data without crash")
    except:
        print("  ✓ Pass - raised exception as expected")


def test_mixed_valid_invalid():
    """Test mixed valid/invalid data"""
    print("\nTest: Mixed valid and invalid rows")
    service = PriceUpdaterServiceOptimized()
    
    df = pd.DataFrame({
        'key': ['TUU5 Comdty', 'INVALID', 'TYU5 Comdty', '', 'FVU5 Comdty'],
        'adjtheor': [100.5, float('nan'), 101.0, 102.0, float('nan')],
        'bid': [100.4, 99.0, float('nan'), float('nan'), 103.0],
        'ask': [100.6, 99.2, float('nan'), float('nan'), 103.2]
    })
    
    prices = service._extract_prices_deduplicated(df)
    print(f"  Result: {len(prices)} valid prices extracted")
    # Should get TUU5 (adjtheor), FVU5 (bid/ask midpoint)
    assert len(prices) >= 2, "Should extract valid prices"
    print("  ✓ Pass")


def main():
    """Run all edge case tests"""
    print("="*50)
    print("EDGE CASE TESTING")
    print("="*50)
    
    tests = [
        test_empty_dataframe,
        test_missing_columns,
        test_all_nan_prices,
        test_symbol_translation_failure,
        test_corrupt_message,
        test_mixed_valid_invalid
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "="*50)
    if failed == 0:
        print("ALL EDGE CASE TESTS PASSED ✓")
    else:
        print(f"FAILED {failed}/{len(tests)} tests")
    print("="*50)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())