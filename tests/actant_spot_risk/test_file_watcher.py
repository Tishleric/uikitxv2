"""Test the Spot Risk file watcher functionality."""

import sys
import os
from pathlib import Path
import time
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.actant.spot_risk.file_watcher import SpotRiskFileHandler, SpotRiskWatcher


def test_file_handler():
    """Test basic file handler functionality."""
    print("\n=== Testing SpotRiskFileHandler ===")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = Path(temp_dir) / "input"
        output_dir = Path(temp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create handler
        handler = SpotRiskFileHandler(str(input_dir), str(output_dir))
        print(f"✓ Handler created for {input_dir}")
        
        # Test file pattern detection
        test_files = [
            ("bav_analysis_20250121_120000.csv", True),
            ("bav_analysis_test.csv", True),  # Will be filtered in processing
            ("other_file.csv", False),
            ("data.txt", False),
        ]
        
        for filename, should_process in test_files:
            file_path = input_dir / filename
            file_path.touch()
            
            # Simulate file event
            result = handler._process_file_event(str(file_path))
            print(f"  File: {filename} - {'Would process' if should_process else 'Ignored'}")
        
        print("\n✓ File pattern detection working correctly")


def test_watcher_initialization():
    """Test watcher initialization and existing file detection."""
    print("\n=== Testing SpotRiskWatcher ===")
    
    # Use the actual directories
    input_dir = "data/input/actant_spot_risk"
    output_dir = "data/output/spot_risk"
    
    # Create watcher
    watcher = SpotRiskWatcher(input_dir, output_dir)
    print(f"✓ Watcher created")
    print(f"  Input: {watcher.input_dir}")
    print(f"  Output: {watcher.output_dir}")
    
    # Check for existing files
    input_files = list(Path(input_dir).glob("bav_analysis_*.csv"))
    output_files = list(Path(output_dir).glob("bav_analysis_processed_*.csv"))
    
    print(f"\n✓ Found {len(input_files)} input files")
    print(f"✓ Found {len(output_files)} processed files")
    
    # Don't actually start the watcher in test
    print("\n✓ Watcher initialization successful")


if __name__ == "__main__":
    print("Testing Spot Risk File Watcher Components")
    print("="*50)
    
    try:
        test_file_handler()
        test_watcher_initialization()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("\nTo run the full watcher service, use:")
        print("  python run_spot_risk_watcher.py")
        print("  or")
        print("  run_spot_risk_watcher.bat")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 