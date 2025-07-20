#!/usr/bin/env python3
"""
Check format consistency for all weekly options (Monday-Thursday).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from pathlib import Path
from collections import defaultdict

def main():
    """Check all weekly option formats."""
    
    print("="*60)
    print("CHECKING ALL WEEKLY OPTION FORMATS")
    print("="*60)
    
    db_path = Path("data/output/market_prices/market_prices.db")
    conn = sqlite3.connect(str(db_path))
    
    # Define expected Bloomberg patterns for each weekday
    weekday_patterns = {
        'Monday': ['VBY'],
        'Tuesday': ['TJP'], 
        'Wednesday': ['TYY', 'TYW'],  # Check both
        'Thursday': ['TJW'],
        'Friday': ['3M', 'MA']  # Both formats
    }
    
    print("\n1. CHECKING SYMBOL PATTERNS BY WEEKDAY")
    print("-" * 50)
    
    for weekday, patterns in weekday_patterns.items():
        print(f"\n{weekday} options:")
        
        for pattern in patterns:
            # Count symbols with this pattern
            if 'MA' in pattern:
                query = f"SELECT COUNT(DISTINCT symbol) FROM options_prices WHERE symbol LIKE '%{pattern} %'"
            else:
                query = f"SELECT COUNT(DISTINCT symbol) FROM options_prices WHERE symbol LIKE '{pattern}%'"
            
            count = pd.read_sql_query(query, conn).iloc[0, 0]
            print(f"  {pattern}: {count} unique symbols")
            
            # Show examples
            if 'MA' in pattern:
                query = f"SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '%{pattern} %' LIMIT 3"
            else:
                query = f"SELECT DISTINCT symbol FROM options_prices WHERE symbol LIKE '{pattern}%' LIMIT 3"
                
            examples = pd.read_sql_query(query, conn)
            for symbol in examples['symbol']:
                print(f"    {symbol}")
    
    # 2. Check for overlaps by price type
    print("\n2. CHECKING PRICE OVERLAPS BY PATTERN")
    print("-" * 50)
    
    # Get all unique symbols with their price availability
    query = """
        SELECT 
            symbol,
            MAX(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            MAX(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
            MAX(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior
        FROM options_prices
        GROUP BY symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Categorize by pattern
    pattern_stats = defaultdict(lambda: {'total': 0, 'current_only': 0, 'flash_only': 0, 'both': 0, 'all_three': 0})
    
    for _, row in df.iterrows():
        symbol = row['symbol']
        
        # Determine pattern
        if 'MA ' in symbol:
            pattern = 'Friday (MA)'
        elif symbol.startswith('3MN'):
            pattern = 'Friday (3MN)'
        elif symbol.startswith('VBY'):
            pattern = 'Monday (VBY)'
        elif symbol.startswith('TJP'):
            pattern = 'Tuesday (TJP)'
        elif symbol.startswith('TYY'):
            pattern = 'Wednesday (TYY)'
        elif symbol.startswith('TYW'):
            pattern = 'Wednesday (TYW)'
        elif symbol.startswith('TJW'):
            pattern = 'Thursday (TJW)'
        elif symbol.startswith('1MQ'):
            pattern = 'Other (1MQ)'
        else:
            pattern = 'Other'
            
        stats = pattern_stats[pattern]
        stats['total'] += 1
        
        if row['has_current'] and not row['has_flash']:
            stats['current_only'] += 1
        elif row['has_flash'] and not row['has_current']:
            stats['flash_only'] += 1
        elif row['has_current'] and row['has_flash']:
            stats['both'] += 1
            
        if row['has_current'] and row['has_flash'] and row['has_prior']:
            stats['all_three'] += 1
    
    # Display results
    print("\nPattern statistics:")
    print(f"{'Pattern':<20} {'Total':<8} {'Current Only':<13} {'Flash Only':<12} {'Both':<8} {'All Three':<10}")
    print("-" * 80)
    
    for pattern, stats in sorted(pattern_stats.items()):
        print(f"{pattern:<20} {stats['total']:<8} {stats['current_only']:<13} {stats['flash_only']:<12} {stats['both']:<8} {stats['all_three']:<10}")
    
    # 3. Check specific overlaps
    print("\n3. SYMBOLS WITH ALL THREE PRICES")
    print("-" * 50)
    
    query = """
        SELECT symbol, Current_Price, Flash_Close, prior_close
        FROM options_prices
        WHERE Current_Price IS NOT NULL 
        AND Flash_Close IS NOT NULL 
        AND prior_close IS NOT NULL
        ORDER BY symbol
        LIMIT 20
    """
    
    results = pd.read_sql_query(query, conn)
    
    if len(results) > 0:
        print("Symbols with all three prices:")
        for _, row in results.iterrows():
            print(f"  {row['symbol']}: Current=${row['Current_Price']:.4f}, Flash=${row['Flash_Close']:.4f}, Prior=${row['prior_close']:.4f}")
    else:
        print("No symbols have all three prices yet.")
    
    # 4. Check Wednesday format issue (TYY vs TYW)
    print("\n4. WEDNESDAY FORMAT CHECK")
    print("-" * 50)
    
    # Our translator now uses TYY, but check what's in the database
    wed_query = """
        SELECT 
            CASE 
                WHEN symbol LIKE 'TYY%' THEN 'TYY format'
                WHEN symbol LIKE 'TYW%' THEN 'TYW format'
            END as format,
            COUNT(DISTINCT symbol) as symbols,
            SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash
        FROM options_prices
        WHERE symbol LIKE 'TYY%' OR symbol LIKE 'TYW%'
        GROUP BY format
    """
    
    wed_results = pd.read_sql_query(wed_query, conn)
    print("Wednesday option formats:")
    print(wed_results)
    
    conn.close()


if __name__ == "__main__":
    main() 