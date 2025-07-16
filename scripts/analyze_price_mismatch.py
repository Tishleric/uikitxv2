"""Analyze the mismatch between translated symbols and price file symbols."""

import sys
sys.path.append('.')
import pandas as pd
import sqlite3

print("=== ANALYZING PRICE SYMBOL MISMATCH ===\n")

# Read a sample options price file
options_file = "data/input/market_prices/options/Options_20250714_1600.csv"
print(f"Reading {options_file}...")
df = pd.read_csv(options_file)

print(f"\nColumns in price file: {list(df.columns)}")
print(f"Number of rows: {len(df)}")

# Show sample symbols
print("\nSample option symbols from price file:")
for symbol in df['SYMBOL'].head(10):
    print(f"  • {symbol}")

# Check what's in our database
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

print("\n\nChecking what's stored in market_prices table:")
cursor.execute("SELECT DISTINCT bloomberg FROM market_prices WHERE bloomberg LIKE 'VBY%' LIMIT 5")
vby_symbols = cursor.fetchall()
print(f"VBY symbols in database: {len(vby_symbols)}")
for row in vby_symbols:
    print(f"  • {row[0]}")

# The issue: Our translator generates "VBYN25C2" but the price files have "3MN5C 110.250 Comdty"
print("\n\nTHE ISSUE:")
print("• SymbolTranslator generates: VBYN25C2 110.750 Comdty")
print("• Price files contain: 3MN5C 110.750 Comdty")
print("\nThe price files use a different format than what our translator expects!")

# Let's see if we can find patterns
print("\n\nAnalyzing option symbols in price file:")
# Group by pattern
symbol_patterns = {}
for symbol in df['SYMBOL']:
    if pd.notna(symbol):
        # Extract the base pattern (before the strike price)
        parts = str(symbol).split()
        if parts:
            base = parts[0]
            pattern = base[:4] if len(base) >= 4 else base
            if pattern not in symbol_patterns:
                symbol_patterns[pattern] = []
            symbol_patterns[pattern].append(symbol)

print("\nSymbol patterns found:")
for pattern, symbols in sorted(symbol_patterns.items()):
    print(f"  {pattern}: {len(symbols)} symbols")
    # Show a few examples
    for s in symbols[:3]:
        print(f"    - {s}")

conn.close()

print("\n\nCONCLUSION:")
print("The price files use a simplified Bloomberg format (e.g., '3MN5C 110.750 Comdty')")
print("But our translator generates the full format (e.g., 'VBYN25C2 110.750 Comdty')")
print("We need to either:")
print("1. Modify the translator to match the price file format")
print("2. Create a mapping between the two formats")
print("3. Process price files differently to use full Bloomberg symbols") 