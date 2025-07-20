#!/usr/bin/env python3
"""
ACTIVE Script: Generate and Inspect TYU5 Market Prices DataFrame

This script creates the exact DataFrame that TYU5 expects for market prices,
showing the Flash_Close column and proper symbol formatting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
from lib.trading.market_prices import MarketPriceStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_tyu5_market_prices_dataframe():
    """Generate the market prices DataFrame exactly as TYU5 expects it."""
    
    logger.info("=" * 80)
    logger.info("GENERATING TYU5 MARKET PRICES DATAFRAME")
    logger.info("=" * 80)
    
    # Create TYU5 adapter instance
    adapter = TYU5Adapter()
    
    # Get market prices in TYU5 format
    logger.info("\nFetching market prices from database and converting to TYU5 format...")
    market_prices_df = adapter.get_market_prices()
    
    # Display DataFrame info
    logger.info(f"\nDataFrame Shape: {market_prices_df.shape}")
    logger.info(f"Columns: {list(market_prices_df.columns)}")
    logger.info(f"Data Types:\n{market_prices_df.dtypes}")
    
    # Display the full DataFrame
    logger.info("\nFull TYU5 Market Prices DataFrame:")
    logger.info("=" * 80)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    if not market_prices_df.empty:
        print(market_prices_df.to_string(index=False))
        
        # Save to CSV for further inspection
        output_path = Path("data/output/tyu5_market_prices_dataframe.csv")
        market_prices_df.to_csv(output_path, index=False)
        logger.info(f"\nDataFrame saved to: {output_path}")
        
        # Show some statistics
        logger.info("\n" + "=" * 80)
        logger.info("DATAFRAME STATISTICS")
        logger.info("=" * 80)
        
        # Group by asset type
        if 'asset_type' in market_prices_df.columns:
            logger.info("\nCounts by Asset Type:")
            print(market_prices_df['asset_type'].value_counts())
        
        # Show sample rows
        logger.info("\n" + "=" * 80)
        logger.info("SAMPLE ROWS")
        logger.info("=" * 80)
        
        logger.info("\nFirst 5 Futures:")
        futures_df = market_prices_df[market_prices_df['Symbol'].apply(lambda x: ' ' not in str(x))]
        if not futures_df.empty:
            print(futures_df.head().to_string(index=False))
        
        logger.info("\nFirst 5 Options:")
        options_df = market_prices_df[market_prices_df['Symbol'].apply(lambda x: ' ' in str(x))]
        if not options_df.empty:
            print(options_df.head().to_string(index=False))
        
        # Verify column values
        logger.info("\n" + "=" * 80)
        logger.info("COLUMN VALUE VERIFICATION")
        logger.info("=" * 80)
        
        logger.info("\nFlash_Close column statistics:")
        print(f"  Non-null count: {market_prices_df['Flash_Close'].notna().sum()}")
        print(f"  Null count: {market_prices_df['Flash_Close'].isna().sum()}")
        if market_prices_df['Flash_Close'].notna().any():
            print(f"  Min value: {market_prices_df['Flash_Close'].min()}")
            print(f"  Max value: {market_prices_df['Flash_Close'].max()}")
            print(f"  Mean value: {market_prices_df['Flash_Close'].mean():.4f}")
        
        logger.info("\nPrior_Close column statistics:")
        print(f"  Non-null count: {market_prices_df['Prior_Close'].notna().sum()}")
        print(f"  Null count: {market_prices_df['Prior_Close'].isna().sum()}")
        
    else:
        logger.warning("DataFrame is empty! No market prices found.")
        
        # Check database directly
        logger.info("\nChecking database directly...")
        storage = MarketPriceStorage()
        summary = storage.get_summary()
        logger.info(f"Database summary: {summary}")
    
    return market_prices_df

def show_raw_database_data():
    """Show raw data from the database for comparison."""
    logger.info("\n" + "=" * 80)
    logger.info("RAW DATABASE DATA (for comparison)")
    logger.info("=" * 80)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        
        # Show futures data
        logger.info("\nRaw Futures Prices (first 5):")
        futures_df = pd.read_sql("SELECT * FROM futures_prices LIMIT 5", conn)
        if not futures_df.empty:
            print(futures_df.to_string())
        
        # Show options data
        logger.info("\nRaw Options Prices (first 5):")
        options_df = pd.read_sql("SELECT * FROM options_prices LIMIT 5", conn)
        if not options_df.empty:
            print(options_df.to_string())
        
        conn.close()
    else:
        logger.warning(f"Database not found at {db_path}")

def demonstrate_tyu5_usage(market_prices_df):
    """Show how TYU5 would use this DataFrame."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATING TYU5 USAGE")
    logger.info("=" * 80)
    
    if not market_prices_df.empty:
        # Simulate what TYU5's PositionCalculator does
        logger.info("\nTYU5 PositionCalculator would process like this:")
        logger.info("```python")
        logger.info("for _, row in market_prices_df.iterrows():")
        logger.info("    symbol = row['Symbol']")
        logger.info("    self.current_prices[symbol] = price_to_decimal(row['Flash_Close'])")
        logger.info("    self.prior_close_prices[symbol] = price_to_decimal(row['Prior_Close'])")
        logger.info("```")
        
        # Show example processing of first row
        if len(market_prices_df) > 0:
            first_row = market_prices_df.iloc[0]
            logger.info(f"\nExample with first row:")
            logger.info(f"  Symbol: {first_row['Symbol']}")
            logger.info(f"  Flash_Close: {first_row['Flash_Close']}")
            logger.info(f"  Prior_Close: {first_row['Prior_Close']}")

if __name__ == "__main__":
    # Generate and inspect the DataFrame
    market_prices_df = generate_tyu5_market_prices_dataframe()
    
    # Show raw database data for comparison
    show_raw_database_data()
    
    # Demonstrate how TYU5 uses this data
    demonstrate_tyu5_usage(market_prices_df)
    
    logger.info("\n" + "=" * 80)
    logger.info("INSPECTION COMPLETE")
    logger.info("=" * 80) 