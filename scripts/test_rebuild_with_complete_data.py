"""
Test script to run P&L rebuild with complete trade data.
This temporarily replaces the Aug 1 trade file to test position calculations.
"""

import shutil
import os
import subprocess
import sys

def test_with_complete_data():
    """Test P&L rebuild with complete trade data."""
    # Backup original file
    original_file = 'data/input/trade_ledger/trades_20250801.csv'
    backup_file = 'data/input/trade_ledger/trades_20250801_original.csv'
    complete_file = 'data/input/trade_ledger/trades_20250801_complete.csv'
    
    print("=== Testing P&L Rebuild with Complete Trade Data ===")
    
    try:
        # Backup original
        if not os.path.exists(backup_file):
            shutil.copy2(original_file, backup_file)
            print(f"Backed up original to: {backup_file}")
        
        # Replace with complete data
        shutil.copy2(complete_file, original_file)
        print(f"Replaced trade file with complete data")
        
        # Run the rebuild script
        print("\nRunning P&L rebuild...")
        result = subprocess.run([
            sys.executable,
            'scripts/rebuild_historical_pnl.py'
        ], capture_output=True, text=True)
        
        # Show last 50 lines of output
        output_lines = result.stdout.strip().split('\n')
        print("\n=== P&L Rebuild Output (last 50 lines) ===")
        for line in output_lines[-50:]:
            print(line)
            
        if result.stderr:
            print("\n=== Errors ===")
            print(result.stderr)
            
    finally:
        # Always restore original
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, original_file)
            print("\nRestored original trade file")

if __name__ == "__main__":
    test_with_complete_data()