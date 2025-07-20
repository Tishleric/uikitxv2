#!/usr/bin/env python3
"""
ACTIVE Script: Test Flash_Close Format in TYU5 Adapter
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter

print("Testing TYU5Adapter with Flash_Close...")
print("=" * 80)

# Create adapter
adapter = TYU5Adapter()

# Get market prices
try:
    df = adapter.get_market_prices()
    
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check if Flash_Close column exists
    if 'Flash_Close' in df.columns:
        print("\n✓ SUCCESS: Flash_Close column found!")
    else:
        print("\n✗ ERROR: Flash_Close column missing!")
        print(f"  Found columns: {list(df.columns)}")
        
    # Show sample data if available
    if not df.empty:
        print("\nFirst 5 rows:")
        print(df.head().to_string(index=False))
    else:
        print("\nDataFrame is empty - no market prices in database")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete.") 