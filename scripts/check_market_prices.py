#!/usr/bin/env python3
"""Check market prices loading."""
import sqlite3

# Check raw data
conn = sqlite3.connect('data/output/market_prices/market_prices.db')
cursor = conn.cursor()

print("Market Prices for TYU5:")
cursor.execute("SELECT symbol, Flash_Close, prior_close, trade_date FROM futures_prices WHERE symbol = 'TYU5' ORDER BY trade_date DESC")
for row in cursor.fetchall():
    print(f"  {row}")

# Test loading through adapter
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.fullpnl.data_sources import MarketPricesDatabase
from pathlib import Path

mp_db = MarketPricesDatabase(Path('data/output/market_prices/market_prices.db'))

# Debug: check futures processing
futures_symbols = ['TYU5']  # Without ' Comdty'
print(f"\nTesting with futures_symbols: {futures_symbols}")
futures_prices = mp_db._get_futures_prices(futures_symbols, None)
print(f"Futures prices: {futures_prices}")

# Debug: Step through get_latest_prices
symbols = ['TYU5 Comdty']
futures_symbols = [s.replace(' Comdty', '') for s in symbols if not any(x in s for x in ['C', 'P'])]
print(f"\nExtracted futures_symbols: {futures_symbols}")

# Full test
prices = mp_db.get_latest_prices(['TYU5 Comdty'])
print(f"\nFull test prices: {prices}")
print(f"Empty? {len(prices) == 0}")

conn.close() 