#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

# Check July 21 entries
cursor.execute("""
    SELECT symbol, Current_Price, Flash_Close, prior_close 
    FROM options_prices 
    WHERE trade_date = '2025-07-21' 
    LIMIT 5
""")
rows = cursor.fetchall()
print('July 21 entries (should be from July 20 4pm file):')
for row in rows:
    print(f'  {row}')

# Check if spot risk created these
cursor.execute("""
    SELECT COUNT(*) 
    FROM options_prices 
    WHERE trade_date = '2025-07-21' 
    AND Current_Price IS NOT NULL
    AND Flash_Close IS NULL
    AND prior_close IS NULL
""")
spot_risk_count = cursor.fetchone()[0]
print(f'\nSpot risk created entries: {spot_risk_count}')

# Check if 4pm file created these
cursor.execute("""
    SELECT COUNT(*) 
    FROM options_prices 
    WHERE trade_date = '2025-07-21' 
    AND prior_close IS NOT NULL
""")
prior_close_count = cursor.fetchone()[0]
print(f'4pm file created entries: {prior_close_count}')

conn.close() 