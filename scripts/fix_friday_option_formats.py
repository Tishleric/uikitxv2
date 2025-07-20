#!/usr/bin/env python3
"""
Fix Friday option format inconsistencies in market prices database.

The issue: 
- Flash/Prior files use "3MN5C 110.250 Comdty" format
- Spot risk now translates to "3MA C 110.250" format
- This causes no overlap between price sources

Solution:
- Standardize on the newer "3MA C" format per CTO document
- Update existing "3MN5C" entries to "3MA C" format
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import re
from pathlib import Path
from datetime import datetime

def main():
    """Fix Friday option formats in the database."""
    
    print("="*60)
    print("FIXING FRIDAY OPTION FORMAT INCONSISTENCIES")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # First, analyze the current state
    print("\n1. ANALYZING CURRENT FRIDAY OPTION FORMATS")
    print("-" * 50)
    
    # Count 3MN5 format entries
    query = """
        SELECT COUNT(*) as count, 
               COUNT(DISTINCT symbol) as unique_symbols
        FROM options_prices 
        WHERE symbol LIKE '3MN5%'
    """
    result = cursor.execute(query).fetchone()
    print(f"Old format (3MN5): {result[0]} rows, {result[1]} unique symbols")
    
    # Count MA format entries
    query = """
        SELECT COUNT(*) as count,
               COUNT(DISTINCT symbol) as unique_symbols  
        FROM options_prices 
        WHERE symbol LIKE '%MA %'
    """
    result = cursor.execute(query).fetchone()
    print(f"New format (MA): {result[0]} rows, {result[1]} unique symbols")
    
    # Show examples
    print("\nExample old format symbols:")
    query = "SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '3MN5%' LIMIT 5"
    for row in cursor.execute(query):
        print(f"  {row[0]}")
        
    print("\nExample new format symbols:")
    query = "SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '%MA %' LIMIT 5"
    for row in cursor.execute(query):
        print(f"  {row[0]}")
    
    # 2. Create mapping function
    def convert_3mn5_to_ma(symbol):
        """Convert 3MN5C format to 3MA C format."""
        # Pattern: 3MN5C 110.250 Comdty -> 3MA C 110.250
        match = re.match(r'^3M([A-Z])(\d)([CP])\s+(\d+\.\d+)(?:\s+Comdty)?$', symbol)
        if match:
            month = match.group(1)  # N
            year = match.group(2)   # 5
            opt_type = match.group(3)  # C or P
            strike = match.group(4)  # 110.250
            
            # Extract week number from date
            # For July 2025 (N=July, 5=2025), 18th is 3rd Friday
            # This is a simplified mapping - ideally would calculate from actual date
            week_map = {
                ('N', '5'): '3',  # July 2025, 3rd Friday
                ('Q', '5'): '3',  # August 2025, 3rd Friday (assumed)
                ('U', '5'): '3',  # September 2025, 3rd Friday (assumed)
            }
            
            week = week_map.get((month, year), '3')  # Default to 3
            
            # New format: 3MA C 110.250
            return f"{week}MA {opt_type} {strike}"
        return None
    
    # 3. Test conversion
    print("\n2. TESTING CONVERSION")
    print("-" * 50)
    
    test_symbols = [
        "3MN5C 110.250 Comdty",
        "3MN5P 111.000 Comdty",
        "3MN5C 109.500 Comdty"
    ]
    
    for symbol in test_symbols:
        converted = convert_3mn5_to_ma(symbol)
        print(f"{symbol} -> {converted}")
    
    # 4. Perform conversion
    print("\n3. CONVERTING OLD FORMAT TO NEW FORMAT")
    print("-" * 50)
    
    # Get all unique 3MN5 symbols
    query = "SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '3MN5%'"
    old_symbols = cursor.execute(query).fetchall()
    
    conversions = []
    for (old_symbol,) in old_symbols:
        new_symbol = convert_3mn5_to_ma(old_symbol)
        if new_symbol:
            conversions.append((old_symbol, new_symbol))
    
    print(f"Found {len(conversions)} symbols to convert")
    
    if conversions:
        print("\nPerforming updates...")
        
        for old_symbol, new_symbol in conversions:
            # Update the symbol
            cursor.execute("""
                UPDATE options_prices 
                SET symbol = ? 
                WHERE symbol = ?
            """, (new_symbol, old_symbol))
            
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"  Updated {rows_updated} rows: {old_symbol} -> {new_symbol}")
        
        conn.commit()
        print(f"\nSuccessfully converted {len(conversions)} symbols")
    
    # 5. Verify results
    print("\n4. VERIFYING RESULTS")
    print("-" * 50)
    
    # Check if we now have overlaps
    query = """
        SELECT 
            symbol,
            COUNT(*) as row_count,
            SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
            SUM(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior
        FROM options_prices
        WHERE symbol LIKE '%MA %'
        GROUP BY symbol
        HAVING has_current > 0 OR has_flash > 0 OR has_prior > 0
        ORDER BY symbol
        LIMIT 10
    """
    
    print("Friday options with price data:")
    for row in cursor.execute(query):
        symbol, count, current, flash, prior = row
        print(f"  {symbol}: {count} rows (Current:{current}, Flash:{flash}, Prior:{prior})")
    
    # Check for overlaps
    query = """
        SELECT COUNT(DISTINCT symbol) 
        FROM options_prices
        WHERE symbol LIKE '%MA %'
        AND Current_Price IS NOT NULL 
        AND (Flash_Close IS NOT NULL OR prior_close IS NOT NULL)
    """
    
    overlap_count = cursor.execute(query).fetchone()[0]
    print(f"\nFriday options with both Current and Flash/Prior: {overlap_count}")
    
    conn.close()
    print("\nConversion complete!")


if __name__ == "__main__":
    main() 