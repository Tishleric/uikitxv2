"""Check what symbols exist in market prices database."""

import sqlite3

conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("=== MARKET PRICES SYMBOLS CHECK ===\n")

# Check futures
print("FUTURES PRICES:")
cursor.execute("SELECT DISTINCT symbol FROM futures_prices ORDER BY symbol")
futures = cursor.fetchall()
for (symbol,) in futures:
    print(f"  {symbol}")

# Check for our specific symbols
print("\n\nSPECIFIC QUERIES:")
print("-" * 40)

# TYU5
cursor.execute("SELECT symbol, current_price, prior_close FROM futures_prices WHERE symbol LIKE '%TYU5%'")
result = cursor.fetchall()
print(f"TYU5 futures: {result}")

# Options we're looking for
options_to_find = ['3MN5P 110.000', '3MN5P 110.250', 'VBYN25P3 109.500', 'VBYN25P3 110.000', 
                   'VBYN25P3 110.250', 'TYWN25P4 109.750', 'TYWN25P4 110.500']

print("\nOPTIONS PRICES:")
for opt in options_to_find:
    cursor.execute("SELECT symbol, current_price, prior_close FROM options_prices WHERE symbol LIKE ?", (f'%{opt}%',))
    result = cursor.fetchall()
    if result:
        print(f"  {opt}: {result}")
    else:
        print(f"  {opt}: NOT FOUND")

conn.close() 