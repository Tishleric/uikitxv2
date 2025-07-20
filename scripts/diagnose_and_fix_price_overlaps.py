#!/usr/bin/env python3
"""
Diagnose and fix price overlap issues for TYU5 calculations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from pathlib import Path
import re

def main():
    """Diagnose and fix price overlap issues."""
    
    print("="*60)
    print("DIAGNOSING PRICE OVERLAP ISSUES")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db") 
    conn = sqlite3.connect(str(db_path))
    
    # 1. Check Friday options in detail
    print("\n1. FRIDAY OPTIONS DETAILED CHECK")
    print("-" * 50)
    
    query = """
        SELECT 
            symbol,
            trade_date,
            Current_Price,
            Flash_Close,
            prior_close
        FROM options_prices
        WHERE symbol LIKE '%MA %'
        ORDER BY symbol, trade_date
    """
    
    friday_df = pd.read_sql_query(query, conn)
    
    print(f"Total Friday option rows: {len(friday_df)}")
    print("\nSample Friday options:")
    print(friday_df.head(10))
    
    # 2. Check if we're missing prior_close data
    print("\n2. PRIOR_CLOSE DATA CHECK")
    print("-" * 50)
    
    # Check what prior_close data exists
    query = """
        SELECT 
            symbol,
            trade_date,
            prior_close
        FROM options_prices
        WHERE prior_close IS NOT NULL
        AND (symbol LIKE '3MN5%' OR symbol LIKE '%MA %')
        ORDER BY symbol
        LIMIT 10
    """
    
    prior_df = pd.read_sql_query(query, conn)
    print("Friday options with prior_close:")
    print(prior_df)
    
    # 3. Check Flash/Prior file dates vs Current dates
    print("\n3. DATE MISMATCH CHECK")
    print("-" * 50)
    
    query = """
        SELECT DISTINCT trade_date, 
               SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
               SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
               SUM(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior
        FROM options_prices
        GROUP BY trade_date
        ORDER BY trade_date
    """
    
    date_df = pd.read_sql_query(query, conn)
    print("Price availability by date:")
    print(date_df)
    
    # 4. The real issue - Flash/Prior are from different dates!
    print("\n4. FIXING DATE ALIGNMENT")
    print("-" * 50)
    
    # Current prices are from 2025-07-17 (spot risk file)
    # Flash/Prior might be from 2025-07-18 (when files were created)
    
    # Let's check specific symbols across dates
    query = """
        SELECT 
            o1.symbol,
            o1.trade_date as date1,
            o1.Current_Price,
            o2.trade_date as date2,
            o2.Flash_Close,
            o2.prior_close
        FROM options_prices o1
        LEFT JOIN options_prices o2
            ON o1.symbol = o2.symbol
            AND o2.Flash_Close IS NOT NULL
        WHERE o1.Current_Price IS NOT NULL
        AND o1.symbol LIKE '%MA %'
        LIMIT 10
    """
    
    cross_date_df = pd.read_sql_query(query, conn)
    print("Cross-date symbol check:")
    print(cross_date_df)
    
    # 5. Fix by aligning dates
    print("\n5. ALIGNING PRICE DATA ACROSS DATES")
    print("-" * 50)
    
    # For TYU5 testing, we need prices from the same logical trading day
    # Current prices from spot risk (2025-07-17) should match with
    # Flash/Prior from market files (likely labeled 2025-07-18)
    
    cursor = conn.cursor()
    
    # Create a temporary merged view
    query = """
        CREATE TEMPORARY TABLE merged_prices AS
        SELECT 
            COALESCE(c.symbol, f.symbol) as symbol,
            '2025-07-17' as trade_date,  -- Standardize on spot risk date
            c.Current_Price,
            f.Flash_Close,
            f.prior_close
        FROM 
            (SELECT * FROM options_prices WHERE Current_Price IS NOT NULL AND trade_date = '2025-07-17') c
        FULL OUTER JOIN
            (SELECT * FROM options_prices WHERE Flash_Close IS NOT NULL) f
        ON c.symbol = f.symbol
        WHERE COALESCE(c.symbol, f.symbol) IS NOT NULL
    """
    
    # SQLite doesn't support FULL OUTER JOIN, so use UNION approach
    query = """
        CREATE TEMPORARY TABLE merged_prices AS
        SELECT 
            symbol,
            '2025-07-17' as trade_date,
            MAX(Current_Price) as Current_Price,
            MAX(Flash_Close) as Flash_Close,
            MAX(prior_close) as prior_close
        FROM (
            SELECT symbol, Current_Price, NULL as Flash_Close, NULL as prior_close
            FROM options_prices 
            WHERE Current_Price IS NOT NULL AND trade_date = '2025-07-17'
            
            UNION ALL
            
            SELECT symbol, NULL as Current_Price, Flash_Close, prior_close
            FROM options_prices 
            WHERE Flash_Close IS NOT NULL
        )
        GROUP BY symbol
    """
    
    cursor.execute("DROP TABLE IF EXISTS merged_prices")
    cursor.execute(query)
    
    # Check results
    query = """
        SELECT COUNT(*) as total,
               SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL AND prior_close IS NOT NULL THEN 1 ELSE 0 END) as complete
        FROM merged_prices
    """
    
    result = cursor.execute(query).fetchone()
    print(f"Merged table: {result[0]} total symbols, {result[1]} with all three prices")
    
    # Show examples
    query = """
        SELECT symbol, Current_Price, Flash_Close, prior_close
        FROM merged_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
        LIMIT 10
    """
    
    print("\nExamples with all three prices:")
    for row in cursor.execute(query):
        symbol, current, flash, prior = row
        print(f"  {symbol}: Current=${current:.4f}, Flash=${flash:.4f}, Prior=${prior:.4f}")
    
    # 6. Create a consolidated table for TYU5
    print("\n6. CREATING CONSOLIDATED PRICE TABLE")
    print("-" * 50)
    
    cursor.execute("DROP TABLE IF EXISTS consolidated_prices")
    
    cursor.execute("""
        CREATE TABLE consolidated_prices AS
        SELECT * FROM merged_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
    """)
    
    count = cursor.execute("SELECT COUNT(*) FROM consolidated_prices").fetchone()[0]
    print(f"Created consolidated_prices table with {count} complete entries")
    
    # Also check futures
    print("\n7. FUTURES PRICE CHECK")
    print("-" * 50)
    
    query = """
        SELECT 
            symbol,
            trade_date,
            Current_Price,
            Flash_Close,
            prior_close
        FROM futures_prices
        WHERE symbol = 'TYU5'
        ORDER BY trade_date
    """
    
    futures_df = pd.read_sql_query(query, conn)
    print("TYU5 futures prices:")
    print(futures_df)
    
    conn.close()
    print("\nDiagnosis complete!")
    
    # Provide recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    print("\n1. The main issue is that Current_Price (from spot risk) and Flash/Prior")
    print("   (from market files) are on different trade_date values.")
    print("\n2. For TYU5 testing, use the consolidated_prices view created above")
    print("   or manually align the dates when querying.")
    print("\n3. The spot risk file watcher should be configured to use the same")
    print("   trade_date as the Flash/Prior files for consistency.")


if __name__ == "__main__":
    main() 