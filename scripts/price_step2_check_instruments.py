"""Price Step 2: Check instruments in positions vs available prices."""

import sys
sys.path.append('.')
import sqlite3
import pandas as pd
from datetime import datetime

print("=== PRICE STEP 2: CHECKING INSTRUMENT MAPPING ===")
print(f"Time: {datetime.now()}\n")

# 1. Get all instruments from positions
print("1. INSTRUMENTS IN POSITIONS:")
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT instrument_name FROM positions ORDER BY instrument_name")
position_instruments = [row[0] for row in cursor.fetchall()]
print(f"   Found {len(position_instruments)} unique instruments:")
for inst in position_instruments[:10]:  # Show first 10
    print(f"   • {inst}")
if len(position_instruments) > 10:
    print(f"   ... and {len(position_instruments) - 10} more")

# 2. Check what's in market_prices table
print("\n2. INSTRUMENTS IN MARKET_PRICES TABLE:")
cursor.execute("SELECT COUNT(DISTINCT instrument_symbol) FROM market_prices")
price_count = cursor.fetchone()[0]
print(f"   Found {price_count} unique instruments with prices")

cursor.execute("SELECT DISTINCT instrument_symbol FROM market_prices LIMIT 20")
price_instruments = [row[0] for row in cursor.fetchall()]
print("   Sample instruments with prices:")
for inst in price_instruments:
    print(f"   • {inst}")

# 3. Read a sample price file to see the format
print("\n3. SAMPLE PRICE FILE ANALYSIS:")
print("\n   Futures file (Futures_20250715_1400.csv):")
futures_df = pd.read_csv("data/input/market_prices/futures/Futures_20250715_1400.csv")
print(f"   Shape: {futures_df.shape}")
print(f"   Columns: {list(futures_df.columns)}")
if not futures_df.empty:
    print("   Sample data:")
    print(futures_df.head())

print("\n   Options file (Options_20250715_1400.csv):")
options_df = pd.read_csv("data/input/market_prices/options/Options_20250715_1400.csv")
print(f"   Shape: {options_df.shape}")
print(f"   Columns: {list(options_df.columns)}")
if not options_df.empty:
    print("   First few rows:")
    for idx, row in options_df.head(3).iterrows():
        print(f"   {row.to_dict()}")

# 4. Check specific instrument mapping
print("\n4. SPECIFIC INSTRUMENT CHECK:")
test_instrument = "XCMEOPADPS20250716N0WY3/111.25"  # From the error message
print(f"   Looking for: {test_instrument}")

# Check if it exists in positions
cursor.execute("SELECT * FROM positions WHERE instrument_name = ?", (test_instrument,))
pos = cursor.fetchone()
if pos:
    print("   ✓ Found in positions table")
else:
    print("   ❌ Not found in positions table")

# Check if it exists in market_prices
cursor.execute("SELECT * FROM market_prices WHERE instrument_symbol = ?", (test_instrument,))
price = cursor.fetchone()
if price:
    print("   ✓ Found in market_prices table")
else:
    print("   ❌ Not found in market_prices table")
    
    # Try partial matches
    cursor.execute("SELECT DISTINCT instrument_symbol FROM market_prices WHERE instrument_symbol LIKE ?", 
                   ('%' + test_instrument.split('/')[0] + '%',))
    similar = cursor.fetchall()
    if similar:
        print("   Similar instruments in market_prices:")
        for s in similar[:5]:
            print(f"     • {s[0]}")

conn.close()

# 5. Check how instruments are named in price files
print("\n5. INSTRUMENT NAMING IN PRICE FILES:")
if 'SYMBOL' in options_df.columns:
    print("   Option symbols in price file:")
    for symbol in options_df['SYMBOL'].unique()[:10]:
        print(f"   • {symbol}")

print("\n✅ PRICE STEP 2 COMPLETE") 