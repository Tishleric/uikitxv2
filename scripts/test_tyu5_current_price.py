#!/usr/bin/env python3
"""
ACTIVE: Test script to verify TYU5 adapter includes Current_Price column
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
import pandas as pd

def main():
    print("Testing TYU5Adapter with Current_Price column...")
    print("=" * 60)
    
    # Initialize adapter
    adapter = TYU5Adapter()
    
    # Get market prices
    print("\n1. Fetching market prices...")
    market_prices_df = adapter.get_market_prices()
    
    if market_prices_df.empty:
        print("WARNING: No market prices found")
    else:
        print(f"Found {len(market_prices_df)} price records")
        
        # Check columns
        print(f"\nColumns: {list(market_prices_df.columns)}")
        
        # Verify Current_Price column exists
        if 'Current_Price' in market_prices_df.columns:
            print("✅ Current_Price column is present")
        else:
            print("❌ Current_Price column is MISSING")
            
        # Show sample data
        print("\nSample data (first 5 rows):")
        print(market_prices_df.head())
        
        # Check for null values
        print("\nNull value counts:")
        print(market_prices_df[['Symbol', 'Current_Price', 'Flash_Close', 'Prior_Close']].isnull().sum())
        
        # Show some specific examples
        print("\nExample prices:")
        for idx, row in market_prices_df.head(3).iterrows():
            print(f"{row['Symbol']}: Current={row['Current_Price']}, Flash={row['Flash_Close']}, Prior={row['Prior_Close']}")
    
    print("\n" + "=" * 60)
    print("Test complete")

if __name__ == "__main__":
    main() 