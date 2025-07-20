#!/usr/bin/env python3
"""
Comprehensive investigation of market prices data and naming conventions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from pathlib import Path
from collections import defaultdict
import re

def main():
    """Investigate market prices data thoroughly."""
    
    print("="*80)
    print("MARKET PRICES DATA INVESTIGATION")
    print("="*80)
    
    # Connect to database
    db_path = Path("data/output/market_prices/market_prices.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(str(db_path))
    
    # 1. Check overall data coverage
    print("\n1. OVERALL DATA COVERAGE")
    print("-" * 60)
    
    # Options coverage
    query = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT trade_date) as trading_days,
            SUM(CASE WHEN Current_Price IS NOT NULL THEN 1 ELSE 0 END) as has_current,
            SUM(CASE WHEN Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_flash,
            SUM(CASE WHEN prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_prior,
            SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL THEN 1 ELSE 0 END) as has_current_and_flash,
            SUM(CASE WHEN Current_Price IS NOT NULL AND prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_current_and_prior,
            SUM(CASE WHEN Flash_Close IS NOT NULL AND prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_flash_and_prior,
            SUM(CASE WHEN Current_Price IS NOT NULL AND Flash_Close IS NOT NULL AND prior_close IS NOT NULL THEN 1 ELSE 0 END) as has_all_three
        FROM options_prices
    """
    
    df = pd.read_sql_query(query, conn)
    print("Options Price Coverage:")
    for col in df.columns:
        print(f"  {col}: {df[col].iloc[0]:,}")
    
    # Check schema first
    print("\nChecking table schema...")
    query = "PRAGMA table_info(options_prices)"
    schema = pd.read_sql_query(query, conn)
    print("Columns in options_prices:", schema['name'].tolist())
    
    # 2. Sample symbols from each source
    print("\n2. SAMPLE SYMBOLS BY PRICE SOURCE")
    print("-" * 60)
    
    # Current Price symbols
    print("\nSymbols with Current_Price (first 10):")
    query = """
        SELECT DISTINCT symbol, Current_Price
        FROM options_prices 
        WHERE Current_Price IS NOT NULL 
        ORDER BY symbol 
        LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    for _, row in df.iterrows():
        print(f"  {row['symbol']:<30} ${row['Current_Price']:>8.4f}")
    
    # Flash Close symbols
    print("\nSymbols with Flash_Close (first 10):")
    query = """
        SELECT DISTINCT symbol, Flash_Close
        FROM options_prices 
        WHERE Flash_Close IS NOT NULL 
        ORDER BY symbol 
        LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    for _, row in df.iterrows():
        print(f"  {row['symbol']:<30} ${row['Flash_Close']:>8.4f}")
    
    # Prior Close symbols
    print("\nSymbols with prior_close (first 10):")
    query = """
        SELECT DISTINCT symbol, prior_close
        FROM options_prices 
        WHERE prior_close IS NOT NULL 
        ORDER BY symbol 
        LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    for _, row in df.iterrows():
        print(f"  {row['symbol']:<30} ${row['prior_close']:>8.4f}")
    
    # 3. Symbol format analysis
    print("\n3. SYMBOL FORMAT ANALYSIS")
    print("-" * 60)
    
    # Get all unique symbols
    query = "SELECT DISTINCT symbol FROM options_prices"
    all_symbols = pd.read_sql_query(query, conn)['symbol'].tolist()
    
    # Categorize by pattern
    patterns = defaultdict(list)
    
    for symbol in all_symbols[:100]:  # Sample first 100
        if re.match(r'^3M[A-Z]\d[CP]\s+\d+\.\d+\s+Comdty$', symbol):
            patterns['Friday Weekly (3M format)'].append(symbol)
        elif re.match(r'^\dMA\s+[CP]\s+\d+\.\d+$', symbol):
            patterns['Friday Weekly (MA format)'].append(symbol)
        elif re.match(r'^[A-Z]{3}[A-Z]\d{2}[CP]\d\s+\d+\.\d+\s+Comdty$', symbol):
            patterns['Standard Weekly'].append(symbol)
        elif re.match(r'^[A-Z]{3}[A-Z]\d{2}[CP]\s+\d+\.\d+$', symbol):
            patterns['Weekly (no Comdty)'].append(symbol)
        else:
            patterns['Other'].append(symbol)
    
    print("\nSymbol patterns found:")
    for pattern, symbols in patterns.items():
        print(f"\n{pattern}: {len(symbols)} symbols")
        for sym in symbols[:3]:  # Show first 3
            print(f"  {sym}")
        if len(symbols) > 3:
            print(f"  ... and {len(symbols)-3} more")
    
    # 4. Check for potential mapping issues
    print("\n4. POTENTIAL MAPPING ISSUES")
    print("-" * 60)
    
    # Find symbols that appear in different formats
    print("\nChecking for duplicate strikes with different formats...")
    
    # Extract base symbol and strike from each
    symbol_map = defaultdict(list)
    
    for symbol in all_symbols:
        # Try to extract strike price
        strike_match = re.search(r'(\d+\.\d+)', symbol)
        if strike_match:
            strike = strike_match.group(1)
            # Extract option type
            type_match = re.search(r'\s+([CP])\s+', symbol)
            if type_match:
                opt_type = type_match.group(1)
                # Get base symbol (everything before strike)
                base = symbol.split(strike)[0].strip()
                key = f"{base}|{opt_type}|{strike}"
                symbol_map[key].append(symbol)
    
    # Find duplicates
    duplicates = {k: v for k, v in symbol_map.items() if len(v) > 1}
    
    if duplicates:
        print(f"\nFound {len(duplicates)} potential duplicate mappings:")
        for key, symbols in list(duplicates.items())[:5]:
            base, opt_type, strike = key.split('|')
            print(f"\n  Strike {strike} Type {opt_type}:")
            for sym in symbols:
                print(f"    {sym}")
    else:
        print("\nNo obvious duplicate mappings found.")
    
    # 5. Compare Flash/Prior vs Current sources
    print("\n5. SOURCE FILE ANALYSIS")
    print("-" * 60)
    print("(Skipping - no source_file column in table)")
    
    # 6. Look for overlapping symbols between sources
    print("\n6. SYMBOL OVERLAP ANALYSIS")
    print("-" * 60)
    
    # Symbols with Current_Price
    query = "SELECT DISTINCT symbol FROM options_prices WHERE Current_Price IS NOT NULL"
    current_symbols = set(pd.read_sql_query(query, conn)['symbol'].tolist())
    
    # Symbols with Flash_Close
    query = "SELECT DISTINCT symbol FROM options_prices WHERE Flash_Close IS NOT NULL"
    flash_symbols = set(pd.read_sql_query(query, conn)['symbol'].tolist())
    
    # Symbols with prior_close
    query = "SELECT DISTINCT symbol FROM options_prices WHERE prior_close IS NOT NULL"
    prior_symbols = set(pd.read_sql_query(query, conn)['symbol'].tolist())
    
    print(f"\nTotal unique symbols with Current_Price: {len(current_symbols)}")
    print(f"Total unique symbols with Flash_Close: {len(flash_symbols)}")
    print(f"Total unique symbols with prior_close: {len(prior_symbols)}")
    
    # Check overlaps
    current_flash = current_symbols & flash_symbols
    current_prior = current_symbols & prior_symbols
    flash_prior = flash_symbols & prior_symbols
    all_three = current_symbols & flash_symbols & prior_symbols
    
    print(f"\nOverlaps:")
    print(f"  Current ∩ Flash: {len(current_flash)} symbols")
    print(f"  Current ∩ Prior: {len(current_prior)} symbols")
    print(f"  Flash ∩ Prior: {len(flash_prior)} symbols")
    print(f"  All three: {len(all_three)} symbols")
    
    if current_flash:
        print(f"\nExample symbols in both Current and Flash:")
        for sym in list(current_flash)[:5]:
            print(f"  {sym}")
    
    # 7. Check specific date
    print("\n7. SPECIFIC DATE ANALYSIS (2025-07-17)")
    print("-" * 60)
    
    query = """
        SELECT 
            symbol,
            Current_Price,
            Flash_Close,
            prior_close
        FROM options_prices
        WHERE trade_date = '2025-07-17'
        AND (Current_Price IS NOT NULL OR Flash_Close IS NOT NULL OR prior_close IS NOT NULL)
        ORDER BY symbol
        LIMIT 20
    """
    
    df = pd.read_sql_query(query, conn)
    print(f"\nSample data for 2025-07-17:")
    print(df.to_string(index=False))
    
    conn.close()
    
    # 8. Check raw CSV files
    print("\n8. RAW CSV FILE CHECK")
    print("-" * 60)
    
    # Check spot risk CSV
    spot_risk_path = Path("data/input/actant_spot_risk/2025-07-18/bav_analysis_20250717_145100.csv")
    if spot_risk_path.exists():
        print(f"\nSpot Risk CSV: {spot_risk_path}")
        df = pd.read_csv(spot_risk_path, nrows=5)
        print("First few columns:", df.columns.tolist()[:10])
        print("Sample Key values:")
        if 'Key' in df.columns:
            keys = df['Key'].dropna().tolist()
            for key in keys[1:6]:  # Skip header row
                print(f"  {key}")
    
    # Check market price CSVs in Z:\Trade_Control
    market_dirs = [
        Path("Z:/Trade_Control/Options"),
        Path("Z:/Trade_Control/Futures")
    ]
    
    for dir_path in market_dirs:
        if dir_path.exists():
            print(f"\n{dir_path}:")
            csv_files = list(dir_path.glob("*.csv"))[:5]
            for csv_file in csv_files:
                print(f"  {csv_file.name}")
                try:
                    df = pd.read_csv(csv_file, nrows=3)
                    if 'Symbol' in df.columns:
                        print(f"    Sample symbols: {df['Symbol'].tolist()}")
                except:
                    print(f"    Could not read file")


if __name__ == "__main__":
    main() 