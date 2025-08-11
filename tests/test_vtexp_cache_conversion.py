"""
Test VTEXP cache conversion in SpotRiskFileHandler.

This test verifies that VTEXP values are correctly converted from days to years
when loaded by the file watcher's cache refresh mechanism.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import pandas as pd
import multiprocessing
import os
from unittest.mock import Mock

# Import the class we're testing
from lib.trading.actant.spot_risk.file_watcher import SpotRiskFileHandler

def test_vtexp_cache_conversion():
    """Test that VTEXP values are converted from days to years in cache refresh."""
    
    print("=" * 80)
    print("TESTING VTEXP CACHE CONVERSION")
    print("=" * 80)
    
    # Create a temporary VTEXP file with known values
    with tempfile.TemporaryDirectory() as temp_dir:
        vtexp_dir = Path(temp_dir) / 'data' / 'input' / 'vtexp'
        vtexp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test VTEXP data (in days)
        vtexp_data = pd.DataFrame({
            'symbol': ['ZNU5C 110', 'ZNU5C 111', 'ZNU5P 110', 'ZNU5P 111'],
            'vtexp': [1.0, 1.0, 2.0, 3.0]  # Days
        })
        
        vtexp_file = vtexp_dir / 'vtexp_20250805_120000.csv'
        vtexp_data.to_csv(vtexp_file, index=False)
        
        print(f"\nCreated test VTEXP file: {vtexp_file}")
        print("Original VTEXP values (days):")
        print(vtexp_data)
        
        # Create handler with mocked dependencies
        manager = multiprocessing.Manager()
        vtexp_cache = manager.dict({'filepath': None, 'data': None})
        
        handler = SpotRiskFileHandler(
            task_queue=Mock(),
            total_files_per_batch={},
            vtexp_cache=vtexp_cache,
            watcher_ref=Mock()
        )
        
        # Monkey-patch the vtexp directory path for testing
        original_path = Path('data/input/vtexp')
        Path.__new__ = lambda cls, path_str: original_path if path_str == 'data/input/vtexp' else Path(path_str)
        
        # Actually use our test directory
        import glob
        original_glob = glob.glob
        def mock_glob(pattern):
            if 'vtexp_*.csv' in pattern:
                return [str(vtexp_file)]
            return original_glob(pattern)
        glob.glob = mock_glob
        
        # Call the refresh method
        handler._refresh_vtexp_cache()
        
        # Check the cached values
        print("\n✅ Cache refresh completed!")
        print("\nCached VTEXP values (should be in years):")
        
        cached_data = dict(vtexp_cache['data'])
        for symbol, vtexp_years in cached_data.items():
            vtexp_days = vtexp_data[vtexp_data['symbol'] == symbol]['vtexp'].iloc[0]
            expected_years = vtexp_days / 252
            
            print(f"  {symbol}: {vtexp_years:.6f} years (was {vtexp_days} days)")
            
            # Verify conversion
            if abs(vtexp_years - expected_years) < 0.0000001:
                print(f"    ✅ Correctly converted: {vtexp_days} / 252 = {vtexp_years:.6f}")
            else:
                print(f"    ❌ ERROR: Expected {expected_years:.6f}, got {vtexp_years:.6f}")
        
        # Restore original functions
        glob.glob = original_glob
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        # Verify all conversions
        all_correct = True
        for symbol in vtexp_data['symbol']:
            vtexp_days = vtexp_data[vtexp_data['symbol'] == symbol]['vtexp'].iloc[0]
            expected_years = vtexp_days / 252
            actual_years = cached_data[symbol]
            
            if abs(actual_years - expected_years) > 0.0000001:
                all_correct = False
                break
        
        if all_correct:
            print("✅ All VTEXP values correctly converted from days to years!")
        else:
            print("❌ Some VTEXP values were not converted correctly")
            
        return all_correct

if __name__ == "__main__":
    test_vtexp_cache_conversion()