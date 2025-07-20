#!/usr/bin/env python3
"""
Final price alignment for TYU5 testing.

This script properly aligns all price data across different dates and formats
to create a unified view for P&L calculations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from pathlib import Path

def main():
    """Align all price data properly."""
    
    print("="*60)
    print("FINAL PRICE DATA ALIGNMENT")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Create aligned price view
    print("\n1. CREATING ALIGNED PRICE VIEW")
    print("-" * 50)
    
    # Drop existing view/table if exists
    cursor.execute("DROP VIEW IF EXISTS aligned_prices")
    cursor.execute("DROP TABLE IF EXISTS aligned_prices")
    
    # Create a comprehensive view that aligns all prices
    # This handles both the date mismatch and format differences
    query = """
        CREATE TABLE aligned_prices AS
        WITH price_mapping AS (
            -- Map all variations of Friday options
            SELECT 
                CASE 
                    WHEN symbol LIKE '3MN5%' THEN 
                        REPLACE(REPLACE(symbol, '3MN5C', '3MA C'), '3MN5P', '3MA P')
                    ELSE symbol
                END as normalized_symbol,
                symbol as original_symbol,
                trade_date,
                Current_Price,
                Flash_Close,
                prior_close
            FROM options_prices
            
            UNION ALL
            
            -- Also include futures
            SELECT 
                symbol as normalized_symbol,
                symbol as original_symbol,
                trade_date,
                Current_Price,
                Flash_Close,
                prior_close
            FROM futures_prices
        )
        SELECT 
            normalized_symbol as symbol,
            -- Use the logical trading day (spot risk date)
            '2025-07-17' as trade_date,
            -- Aggregate prices across dates
            MAX(CASE WHEN trade_date = '2025-07-17' THEN Current_Price ELSE NULL END) as Current_Price,
            MAX(CASE WHEN trade_date = '2025-07-18' THEN Flash_Close ELSE NULL END) as Flash_Close,
            MAX(CASE WHEN trade_date = '2025-07-18' THEN prior_close ELSE NULL END) as prior_close,
            -- Also keep the original dates for reference
            MAX(CASE WHEN Current_Price IS NOT NULL THEN trade_date ELSE NULL END) as current_date,
            MAX(CASE WHEN Flash_Close IS NOT NULL THEN trade_date ELSE NULL END) as flash_date,
            MAX(CASE WHEN prior_close IS NOT NULL THEN trade_date ELSE NULL END) as prior_date
        FROM price_mapping
        WHERE normalized_symbol NOT LIKE '3MN5%'  -- Exclude old format
        GROUP BY normalized_symbol
    """
    
    cursor.execute(query)
    
    # Check results
    total = cursor.execute("SELECT COUNT(*) FROM aligned_prices").fetchone()[0]
    complete = cursor.execute("""
        SELECT COUNT(*) FROM aligned_prices 
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
    """).fetchone()[0]
    
    print(f"Created aligned_prices table:")
    print(f"  Total symbols: {total}")
    print(f"  Symbols with all three prices: {complete}")
    
    # 2. Show sample data
    print("\n2. SAMPLE ALIGNED DATA")
    print("-" * 50)
    
    query = """
        SELECT symbol, Current_Price, Flash_Close, prior_close
        FROM aligned_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
        ORDER BY symbol
        LIMIT 15
    """
    
    print("\nOptions with all three prices:")
    for row in cursor.execute(query):
        symbol, current, flash, prior = row
        print(f"  {symbol:<25} Current=${current:>8.4f}  Flash=${flash:>8.4f}  Prior=${prior:>8.4f}")
    
    # 3. Check futures specifically
    print("\n3. FUTURES (TYU5) PRICES")
    print("-" * 50)
    
    query = """
        SELECT symbol, Current_Price, Flash_Close, prior_close
        FROM aligned_prices
        WHERE symbol = 'TYU5'
    """
    
    for row in cursor.execute(query):
        symbol, current, flash, prior = row
        if current and flash and prior:
            print(f"{symbol}: Current=${current:.4f}, Flash=${flash:.4f}, Prior=${prior:.4f}")
        else:
            print(f"{symbol}: Current={current}, Flash={flash}, Prior={prior}")
    
    # 4. Create a specific TYU5-ready table
    print("\n4. CREATING TYU5_READY_PRICES TABLE")
    print("-" * 50)
    
    cursor.execute("DROP TABLE IF EXISTS tyu5_ready_prices")
    
    cursor.execute("""
        CREATE TABLE tyu5_ready_prices AS
        SELECT 
            symbol,
            trade_date,
            Current_Price,
            Flash_Close,
            prior_close
        FROM aligned_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
    """)
    
    count = cursor.execute("SELECT COUNT(*) FROM tyu5_ready_prices").fetchone()[0]
    print(f"Created tyu5_ready_prices table with {count} entries ready for P&L calculations")
    
    # 5. Summary by option type
    print("\n5. SUMMARY BY OPTION TYPE")
    print("-" * 50)
    
    query = """
        SELECT 
            CASE 
                WHEN symbol LIKE '%MA C %' THEN 'Friday Call'
                WHEN symbol LIKE '%MA P %' THEN 'Friday Put'
                WHEN symbol LIKE 'VBY%C%' THEN 'Monday Call'
                WHEN symbol LIKE 'VBY%P%' THEN 'Monday Put'
                WHEN symbol LIKE 'TJP%C%' THEN 'Tuesday Call'
                WHEN symbol LIKE 'TJP%P%' THEN 'Tuesday Put'
                WHEN symbol LIKE 'TYY%C%' THEN 'Wednesday Call'
                WHEN symbol LIKE 'TYY%P%' THEN 'Wednesday Put'
                WHEN symbol LIKE 'TJW%C%' THEN 'Thursday Call'
                WHEN symbol LIKE 'TJW%P%' THEN 'Thursday Put'
                WHEN symbol = 'TYU5' THEN 'Futures'
                ELSE 'Other'
            END as option_type,
            COUNT(*) as count
        FROM tyu5_ready_prices
        GROUP BY option_type
        ORDER BY option_type
    """
    
    print("\nReady for TYU5 by type:")
    for row in cursor.execute(query):
        opt_type, count = row
        print(f"  {opt_type:<20} {count:>5}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("ALIGNMENT COMPLETE!")
    print("="*60)
    print("\nThe following tables are now available for TYU5 testing:")
    print("1. aligned_prices - All prices aligned to same date")
    print("2. tyu5_ready_prices - Only symbols with all three prices")
    print("\nUse these tables for your P&L calculations to ensure you have")
    print("Current, Flash, and Prior prices for proper attribution.")


if __name__ == "__main__":
    main() 