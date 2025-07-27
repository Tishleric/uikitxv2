#!/usr/bin/env python3
"""
Test incremental trade processing
"""

import csv
import time
from datetime import datetime
from pathlib import Path

def create_test_trade_file():
    """Create a test trade file and append trades incrementally"""
    
    test_file = Path("data/input/trade_ledger/trades_test_20250101.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create initial file with header and one trade
    with open(test_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tradeId', 'instrumentName', 'marketTradeTime', 'buySell', 'quantity', 'price'])
        writer.writerow([100, 'XCMEFFDPSX20250919U0ZN', '2025-01-01 10:00:00.000', 'B', 1.0, 110.5])
    
    print(f"Created test file with 1 trade: {test_file}")
    print("Watch this file with the trade ledger watcher...")
    print("Press Enter to add another trade...")
    input()
    
    # Append a second trade
    with open(test_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([101, 'XCMEFFDPSX20250919U0ZN', '2025-01-01 10:05:00.000', 'S', 1.0, 110.75])
    
    print("Added second trade")
    print("Press Enter to add a third trade...")
    input()
    
    # Append a third trade
    with open(test_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([102, 'XCMEFFDPSX20250919U0ZN', '2025-01-01 10:10:00.000', 'B', 2.0, 110.625])
    
    print("Added third trade")
    print("Check the logs to verify only new trades were processed each time")

if __name__ == '__main__':
    create_test_trade_file() 