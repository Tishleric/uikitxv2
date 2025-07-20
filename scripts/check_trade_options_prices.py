import sqlite3
import pandas as pd

# Get the symbols from CTO trades
conn = sqlite3.connect('../data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT Symbol 
    FROM cto_trades 
    WHERE Type IN ('CALL', 'PUT')
    ORDER BY Symbol
""")
traded_options = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Traded options: {traded_options}")

# Check if these have prices in market_prices.db
conn = sqlite3.connect('../data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("\nPrice status for traded options on July 18:")
for symbol in traded_options:
    # Try to find exact match first
    cursor.execute("""
        SELECT symbol, Flash_Close, prior_close 
        FROM options_prices 
        WHERE trade_date = '2025-07-18' 
        AND symbol = ?
    """, (symbol,))
    result = cursor.fetchone()
    
    if result:
        print(f"  {symbol}: Flash={result[1]}, Prior={result[2]}")
    else:
        # Try with "Comdty" suffix
        symbol_with_comdty = symbol + " Comdty"
        cursor.execute("""
            SELECT symbol, Flash_Close, prior_close 
            FROM options_prices 
            WHERE trade_date = '2025-07-18' 
            AND symbol = ?
        """, (symbol_with_comdty,))
        result = cursor.fetchone()
        
        if result:
            print(f"  {symbol} (as {result[0]}): Flash={result[1]}, Prior={result[2]}")
        else:
            print(f"  {symbol}: NOT FOUND in market prices!")

conn.close() 