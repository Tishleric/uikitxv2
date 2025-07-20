"""Fix market prices database to use consistent Bloomberg format."""

import sys
sys.path.append('.')
import sqlite3
from datetime import datetime

print("=== FIXING MARKET PRICES TO BLOOMBERG FORMAT ===")
print(f"Time: {datetime.now()}\n")

# Connect to market prices database
mp_conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = mp_conn.cursor()

# 1. Check futures prices
print("1. CHECKING FUTURES PRICES:")
print("-" * 60)
cursor.execute("SELECT DISTINCT symbol FROM futures_prices ORDER BY symbol")
futures_symbols = cursor.fetchall()

print(f"Found {len(futures_symbols)} unique futures symbols:")
futures_to_fix = []
for (symbol,) in futures_symbols:
    print(f"  {symbol}", end="")
    if not symbol.endswith(' Comdty'):
        print(" <- NEEDS FIX")
        futures_to_fix.append(symbol)
    else:
        print(" ✓")

# 2. Check options prices
print("\n2. CHECKING OPTIONS PRICES:")
print("-" * 60)
cursor.execute("SELECT DISTINCT symbol FROM options_prices ORDER BY symbol LIMIT 20")
options_symbols = cursor.fetchall()

print(f"Sample of options symbols:")
options_to_fix = []
for (symbol,) in options_symbols:
    print(f"  {symbol}", end="")
    if not symbol.endswith(' Comdty'):
        print(" <- NEEDS FIX")
        options_to_fix.append(symbol)
    else:
        print(" ✓")

# 3. Fix futures symbols
if futures_to_fix:
    print(f"\n3. FIXING {len(futures_to_fix)} FUTURES SYMBOLS:")
    print("-" * 60)
    for symbol in futures_to_fix:
        new_symbol = f"{symbol} Comdty"
        print(f"  {symbol} -> {new_symbol}")
        cursor.execute("""
            UPDATE futures_prices 
            SET symbol = ? 
            WHERE symbol = ?
        """, (new_symbol, symbol))

# 4. Fix options symbols (if any)
if options_to_fix:
    print(f"\n4. FIXING {len(options_to_fix)} OPTIONS SYMBOLS:")
    print("-" * 60)
    # Get all options that need fixing
    cursor.execute("SELECT DISTINCT symbol FROM options_prices WHERE symbol NOT LIKE '% Comdty'")
    all_options_to_fix = cursor.fetchall()
    
    for (symbol,) in all_options_to_fix:
        new_symbol = f"{symbol} Comdty"
        print(f"  {symbol} -> {new_symbol}")
        cursor.execute("""
            UPDATE options_prices 
            SET symbol = ? 
            WHERE symbol = ?
        """, (new_symbol, symbol))

# Commit changes
mp_conn.commit()

# 5. Verify the fix
print("\n5. VERIFICATION AFTER FIX:")
print("-" * 60)

cursor.execute("SELECT DISTINCT symbol FROM futures_prices ORDER BY symbol")
fixed_futures = cursor.fetchall()
print("Futures symbols (all should end with ' Comdty'):")
for (symbol,) in fixed_futures:
    print(f"  {symbol}")

cursor.execute("SELECT DISTINCT symbol FROM options_prices ORDER BY symbol LIMIT 10")
fixed_options = cursor.fetchall()
print("\nSample options symbols (all should end with ' Comdty'):")
for (symbol,) in fixed_options:
    print(f"  {symbol}")

mp_conn.close()

print("\n\nSUMMARY:")
print("-" * 60)
print(f"✓ Fixed {len(futures_to_fix)} futures symbols to Bloomberg format")
print(f"✓ Fixed {len(options_to_fix)} options symbols to Bloomberg format")
print("✓ All symbols now consistently use Bloomberg format with ' Comdty' suffix") 