#!/usr/bin/env python3
"""
Merge Friday option data from different formats.

Instead of converting symbols, we need to merge the price data 
from old format (3MN5) into new format (MA) entries.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import re
from pathlib import Path
from collections import defaultdict

def main():
    """Merge Friday option data."""
    
    print("="*60)
    print("MERGING FRIDAY OPTION DATA")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Find matching pairs
    print("\n1. FINDING MATCHING FRIDAY OPTION PAIRS")
    print("-" * 50)
    
    # Get all Friday options
    query = """
        SELECT symbol, trade_date, Current_Price, Flash_Close, prior_close
        FROM options_prices
        WHERE symbol LIKE '3MN5%' OR symbol LIKE '%MA %'
        ORDER BY trade_date, symbol
    """
    
    all_friday = cursor.execute(query).fetchall()
    
    # Group by strike and type
    by_strike = defaultdict(list)
    
    for symbol, trade_date, current, flash, prior in all_friday:
        # Extract strike and type
        if 'MA ' in symbol:
            # Format: 3MA C 110.250
            match = re.match(r'^(\d)MA\s+([CP])\s+(\d+\.\d+)$', symbol)
            if match:
                strike = match.group(3)
                opt_type = match.group(2)
                key = (trade_date, strike, opt_type)
                by_strike[key].append({
                    'symbol': symbol,
                    'format': 'new',
                    'current': current,
                    'flash': flash,
                    'prior': prior
                })
        else:
            # Format: 3MN5C 110.250 Comdty
            match = re.match(r'^3MN5([CP])\s+(\d+\.\d+)', symbol)
            if match:
                opt_type = match.group(1)
                strike = match.group(2)
                key = (trade_date, strike, opt_type)
                by_strike[key].append({
                    'symbol': symbol,
                    'format': 'old',
                    'current': current,
                    'flash': flash,
                    'prior': prior
                })
    
    # Find pairs that need merging
    merge_pairs = []
    for key, entries in by_strike.items():
        if len(entries) == 2:
            # We have both formats
            old_entry = next(e for e in entries if e['format'] == 'old')
            new_entry = next(e for e in entries if e['format'] == 'new')
            merge_pairs.append((key, old_entry, new_entry))
    
    print(f"Found {len(merge_pairs)} pairs to merge")
    
    # 2. Merge data
    print("\n2. MERGING PRICE DATA")
    print("-" * 50)
    
    updates = []
    deletes = []
    
    for key, old_entry, new_entry in merge_pairs:
        trade_date, strike, opt_type = key
        
        # Determine what needs updating
        update_fields = []
        update_values = []
        
        # If new entry is missing Flash_Close but old has it
        if new_entry['flash'] is None and old_entry['flash'] is not None:
            update_fields.append("Flash_Close = ?")
            update_values.append(old_entry['flash'])
            
        # If new entry is missing prior_close but old has it  
        if new_entry['prior'] is None and old_entry['prior'] is not None:
            update_fields.append("prior_close = ?")
            update_values.append(old_entry['prior'])
        
        if update_fields:
            updates.append({
                'symbol': new_entry['symbol'],
                'trade_date': trade_date,
                'fields': update_fields,
                'values': update_values,
                'old_symbol': old_entry['symbol']
            })
            
        # Mark old entry for deletion
        deletes.append((old_entry['symbol'], trade_date))
    
    print(f"Will update {len(updates)} entries and remove {len(deletes)} duplicates")
    
    # 3. Execute updates
    if updates:
        print("\nPerforming updates...")
        
        for update in updates:
            # Build update query
            query = f"""
                UPDATE options_prices 
                SET {', '.join(update['fields'])}
                WHERE symbol = ? AND trade_date = ?
            """
            values = update['values'] + [update['symbol'], update['trade_date']]
            
            cursor.execute(query, values)
            if cursor.rowcount > 0:
                print(f"  Updated {update['symbol']} with data from {update['old_symbol']}")
    
    # 4. Delete old format entries
    if deletes:
        print("\nRemoving old format entries...")
        
        for symbol, trade_date in deletes:
            cursor.execute("""
                DELETE FROM options_prices
                WHERE symbol = ? AND trade_date = ?
            """, (symbol, trade_date))
            
            if cursor.rowcount > 0:
                print(f"  Removed {symbol}")
    
    conn.commit()
    
    # 5. Verify results
    print("\n3. VERIFYING RESULTS")
    print("-" * 50)
    
    # Check merged entries
    query = """
        SELECT 
            symbol,
            COUNT(*) as rows,
            SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
            SUM(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior,
            SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_both
        FROM options_prices
        WHERE symbol LIKE '%MA %'
        GROUP BY symbol
        HAVING has_both > 0
        ORDER BY symbol
        LIMIT 10
    """
    
    print("Friday options with both Current and Flash prices:")
    results = cursor.execute(query).fetchall()
    
    if results:
        for symbol, rows, current, flash, prior, both in results:
            print(f"  {symbol}: Current={current}, Flash={flash}, Prior={prior}, Both={both}")
    else:
        print("  No Friday options with both price types yet")
    
    # Check overall statistics
    query = """
        SELECT 
            COUNT(DISTINCT symbol) as symbols_with_all_three
        FROM options_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
    """
    
    count = cursor.execute(query).fetchone()[0]
    print(f"\nTotal symbols with all three prices: {count}")
    
    conn.close()
    print("\nMerge complete!")


if __name__ == "__main__":
    main() 