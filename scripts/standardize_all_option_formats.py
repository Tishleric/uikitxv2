#!/usr/bin/env python3
"""
Standardize all option formats to match CTO document specifications.

Key mappings needed:
1. Friday: 3MN5C -> 3MA C format (already partially done)
2. Wednesday: TYW -> TYY format (per CTO document)
3. Ensure prior_close data is preserved during merging
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def main():
    """Standardize all option formats."""
    
    print("="*60)
    print("STANDARDIZING ALL OPTION FORMATS")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Handle Friday options (complete the merge including prior_close)
    print("\n1. FRIDAY OPTIONS (3MN5 -> MA format)")
    print("-" * 50)
    
    # Find remaining 3MN5 entries that need merging
    query = """
        SELECT o1.symbol as old_symbol, o1.trade_date, o1.Flash_Close, o1.prior_close,
               o2.symbol as new_symbol, o2.Current_Price
        FROM options_prices o1
        LEFT JOIN options_prices o2 
            ON o1.trade_date = o2.trade_date 
            AND SUBSTR(o1.symbol, 5, 1) = SUBSTR(o2.symbol, 5, 1)  -- Option type matches
            AND SUBSTR(o1.symbol, 7) = SUBSTR(o2.symbol, 7)  -- Strike matches
            AND o2.symbol LIKE '%MA %'
        WHERE o1.symbol LIKE '3MN5%'
        AND o1.prior_close IS NOT NULL
    """
    
    friday_merges = cursor.execute(query).fetchall()
    print(f"Found {len(friday_merges)} Friday options with prior_close to merge")
    
    # Update MA format entries with prior_close from 3MN5
    for old_symbol, trade_date, flash, prior, new_symbol, current in friday_merges:
        if new_symbol and prior is not None:
            cursor.execute("""
                UPDATE options_prices
                SET prior_close = ?
                WHERE symbol = ? AND trade_date = ? AND prior_close IS NULL
            """, (prior, new_symbol, trade_date))
            
            if cursor.rowcount > 0:
                print(f"  Updated {new_symbol} with prior_close from {old_symbol}")
    
    # 2. Handle Wednesday options (TYW -> TYY format)
    print("\n2. WEDNESDAY OPTIONS (TYW -> TYY format)")
    print("-" * 50)
    
    # Find Wednesday option pairs
    query = """
        SELECT 
            tyw.symbol as tyw_symbol,
            tyw.trade_date,
            tyw.Flash_Close,
            tyw.prior_close,
            tyy.symbol as tyy_symbol,
            tyy.Current_Price
        FROM options_prices tyw
        LEFT JOIN options_prices tyy
            ON tyw.trade_date = tyy.trade_date
            AND REPLACE(tyw.symbol, 'TYW', 'TYY') = tyy.symbol
        WHERE tyw.symbol LIKE 'TYW%'
    """
    
    wed_pairs = cursor.execute(query).fetchall()
    
    updates = 0
    creates = 0
    
    for tyw_symbol, trade_date, flash, prior, tyy_symbol, current in wed_pairs:
        if tyy_symbol:
            # TYY entry exists - update it with Flash/Prior data
            if flash is not None or prior is not None:
                update_fields = []
                update_values = []
                
                if flash is not None:
                    update_fields.append("Flash_Close = ?")
                    update_values.append(flash)
                    
                if prior is not None:
                    update_fields.append("prior_close = ?")
                    update_values.append(prior)
                
                if update_fields:
                    query = f"""
                        UPDATE options_prices
                        SET {', '.join(update_fields)}
                        WHERE symbol = ? AND trade_date = ?
                    """
                    cursor.execute(query, update_values + [tyy_symbol, trade_date])
                    
                    if cursor.rowcount > 0:
                        updates += 1
                        print(f"  Updated {tyy_symbol} with data from {tyw_symbol}")
        else:
            # No TYY entry - convert TYW to TYY
            tyy_symbol = tyw_symbol.replace('TYW', 'TYY')
            
            # Check if this would create a duplicate
            exists = cursor.execute("""
                SELECT 1 FROM options_prices 
                WHERE symbol = ? AND trade_date = ?
            """, (tyy_symbol, trade_date)).fetchone()
            
            if not exists:
                # Update the symbol
                cursor.execute("""
                    UPDATE options_prices
                    SET symbol = ?
                    WHERE symbol = ? AND trade_date = ?
                """, (tyy_symbol, tyw_symbol, trade_date))
                
                if cursor.rowcount > 0:
                    creates += 1
                    print(f"  Converted {tyw_symbol} -> {tyy_symbol}")
    
    print(f"\nWednesday options: {updates} updated, {creates} converted")
    
    # 3. Clean up remaining old format entries
    print("\n3. CLEANUP")
    print("-" * 50)
    
    # Delete remaining 3MN5 entries that have been merged
    cursor.execute("""
        DELETE FROM options_prices
        WHERE symbol LIKE '3MN5%'
        AND EXISTS (
            SELECT 1 FROM options_prices o2
            WHERE o2.trade_date = options_prices.trade_date
            AND o2.symbol LIKE '%MA %'
            AND SUBSTR(options_prices.symbol, 5, 1) = SUBSTR(o2.symbol, 5, 1)
            AND SUBSTR(options_prices.symbol, 7) = SUBSTR(o2.symbol, 7)
        )
    """)
    
    deleted_friday = cursor.rowcount
    print(f"Deleted {deleted_friday} redundant Friday entries")
    
    # Delete remaining TYW entries that have been merged
    cursor.execute("""
        DELETE FROM options_prices
        WHERE symbol LIKE 'TYW%'
        AND EXISTS (
            SELECT 1 FROM options_prices o2
            WHERE o2.trade_date = options_prices.trade_date
            AND o2.symbol = REPLACE(options_prices.symbol, 'TYW', 'TYY')
        )
    """)
    
    deleted_wed = cursor.rowcount
    print(f"Deleted {deleted_wed} redundant Wednesday entries")
    
    conn.commit()
    
    # 4. Final verification
    print("\n4. FINAL VERIFICATION")
    print("-" * 50)
    
    # Check for symbols with all three prices
    query = """
        SELECT 
            COUNT(DISTINCT symbol) as total_complete,
            SUM(CASE WHEN symbol LIKE '%MA %' THEN 1 ELSE 0 END) as friday_complete,
            SUM(CASE WHEN symbol LIKE 'TYY%' THEN 1 ELSE 0 END) as wednesday_complete
        FROM options_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
    """
    
    result = cursor.execute(query).fetchone()
    print(f"\nOptions with all three prices:")
    print(f"  Total: {result[0]}")
    print(f"  Friday (MA format): {result[1]}")
    print(f"  Wednesday (TYY format): {result[2]}")
    
    # Show examples
    print("\nExample complete entries:")
    query = """
        SELECT symbol, Current_Price, Flash_Close, prior_close
        FROM options_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
        ORDER BY symbol
        LIMIT 5
    """
    
    for row in cursor.execute(query):
        symbol, current, flash, prior = row
        print(f"  {symbol}: Current=${current:.4f}, Flash=${flash:.4f}, Prior=${prior:.4f}")
    
    # Summary statistics
    print("\n5. SUMMARY STATISTICS")
    print("-" * 50)
    
    query = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT symbol) as unique_symbols,
            SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
            SUM(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior,
            SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_current_and_flash,
            SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL AND prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_all_three
        FROM options_prices
    """
    
    stats = cursor.execute(query).fetchone()
    print(f"Total rows: {stats[0]}")
    print(f"Unique symbols: {stats[1]}")
    print(f"Has Current_Price: {stats[2]}")
    print(f"Has Flash_Close: {stats[3]}")
    print(f"Has prior_close: {stats[4]}")
    print(f"Has Current + Flash: {stats[5]}")
    print(f"Has all three: {stats[6]}")
    
    conn.close()
    print("\nStandardization complete!")


if __name__ == "__main__":
    main() 