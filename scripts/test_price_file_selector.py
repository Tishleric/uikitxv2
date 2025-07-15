"""
Test the Price File Selector functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_calculator.price_file_selector import PriceFileSelector, EXPORT_WINDOWS
from datetime import datetime, time
from pathlib import Path
import pytz

def test_filename_parsing():
    """Test parsing of various filename formats."""
    selector = PriceFileSelector()
    
    test_cases = [
        ("Options_20250714_1600.csv", datetime(2025, 7, 14, 16, 0)),
        ("Futures_20250712_1400.csv", datetime(2025, 7, 12, 14, 0)),
        ("market_prices_20250713_1500.csv", datetime(2025, 7, 13, 15, 0)),
        ("Options_20250714_1345.csv", datetime(2025, 7, 14, 13, 45)),
        ("invalid_format.csv", None),
    ]
    
    print("Testing Filename Parsing:")
    print("=" * 60)
    
    for filename, expected_dt in test_cases:
        result = selector.parse_price_filename(filename)
        if expected_dt:
            expected_chicago = selector.chicago_tz.localize(expected_dt)
            success = result == expected_chicago
        else:
            success = result is None
            
        status = "✓" if success else "✗"
        print(f"{status} {filename}")
        if result:
            print(f"   Parsed: {result.strftime('%Y-%m-%d %H:%M %Z')}")
    

def test_time_classification():
    """Test classification of times into export windows."""
    selector = PriceFileSelector()
    chicago_tz = pytz.timezone('America/Chicago')
    
    test_cases = [
        # Time, Expected Window
        (time(13, 30), None),      # Too early for 2pm
        (time(13, 45), '2pm'),     # Start of 2pm window
        (time(14, 0), '2pm'),      # Exactly 2pm
        (time(14, 15), '2pm'),     # Within 2pm window
        (time(14, 30), '2pm'),     # End of 2pm window
        (time(14, 45), None),      # Between windows
        (time(15, 0), None),       # 3pm - should be ignored
        (time(15, 30), None),      # Still 3pm range
        (time(15, 45), '4pm'),     # Start of 4pm window
        (time(16, 0), '4pm'),      # Exactly 4pm
        (time(16, 15), '4pm'),     # Within 4pm window
        (time(16, 30), '4pm'),     # End of 4pm window
        (time(16, 45), None),      # After 4pm window
    ]
    
    print("\nTesting Time Classification:")
    print("=" * 60)
    
    for test_time, expected in test_cases:
        # Create datetime for today with test time
        dt = datetime.combine(datetime.today(), test_time)
        dt_chicago = chicago_tz.localize(dt)
        
        result = selector.classify_export_time(dt_chicago)
        success = result == expected
        status = "✓" if success else "✗"
        
        print(f"{status} {test_time.strftime('%H:%M')} -> {result or 'None':<4} (expected: {expected or 'None'})")


def test_file_selection():
    """Test actual file selection from our data directories."""
    selector = PriceFileSelector()
    base_dir = Path("data/input/market_prices")
    
    print("\nTesting File Selection:")
    print("=" * 60)
    
    # Test at different times of day
    test_times = [
        ("Morning (10am)", datetime(2025, 7, 14, 10, 0)),
        ("After 2pm export (2:45pm)", datetime(2025, 7, 14, 14, 45)),
        ("After 4pm export (4:45pm)", datetime(2025, 7, 14, 16, 45)),
        ("Evening (6pm)", datetime(2025, 7, 14, 18, 0)),
    ]
    
    for desc, test_time in test_times:
        chicago_time = selector.chicago_tz.localize(test_time)
        print(f"\n{desc} - {chicago_time.strftime('%Y-%m-%d %H:%M %Z')}")
        
        results = selector.select_price_files(base_dir, chicago_time)
        
        for asset_type in ['futures', 'options']:
            if asset_type in results:
                info = results[asset_type]
                if 'error' in info:
                    print(f"  {asset_type}: ERROR - {info['error']}")
                else:
                    file_name = info['file'].name
                    price_col = info['price_column']
                    timestamp = info['timestamp'].strftime('%Y-%m-%d %H:%M')
                    print(f"  {asset_type}: {file_name} -> {price_col} (from {timestamp})")


def test_directory_files():
    """Show what files are available and their classifications."""
    selector = PriceFileSelector()
    base_dir = Path("data/input/market_prices")
    
    print("\nAvailable Price Files:")
    print("=" * 60)
    
    for subdir in ['futures', 'options']:
        dir_path = base_dir / subdir
        if dir_path.exists():
            print(f"\n{subdir.upper()}:")
            
            csv_files = sorted(dir_path.glob("*.csv"))
            valid_count = 0
            
            for file_path in csv_files[-10:]:  # Show last 10
                dt = selector.parse_price_filename(file_path.name)
                if dt:
                    window = selector.classify_export_time(dt)
                    if window:
                        valid_count += 1
                        print(f"  ✓ {file_path.name} -> {window} window")
                    else:
                        print(f"  ✗ {file_path.name} -> Invalid time")
                else:
                    print(f"  ? {file_path.name} -> Cannot parse")
                    
            print(f"  Total valid files: {valid_count}")


if __name__ == "__main__":
    test_filename_parsing()
    test_time_classification()
    test_directory_files()
    test_file_selection() 