#!/usr/bin/env python3
"""Debug why 3MN5P options aren't matching spot risk data."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.fullpnl import FULLPNLBuilder
import sqlite3

# Test the matching for 3MN5P 110.000 Comdty
test_symbol = '3MN5P 110.000 Comdty'
print(f"Testing matching for: {test_symbol}")

# Initialize builder
builder = FULLPNLBuilder()

# Get spot risk data for just this symbol
spot_risk_data = builder.spot_risk_db.get_latest_spot_risk_data([test_symbol])
print(f"\nSpot risk data returned: {spot_risk_data}")

# Now let's check what's in the database directly
conn = sqlite3.connect('data/output/spot_risk/spot_risk.db')
cursor = conn.cursor()

# Check for expiry 18JUL25, PUT, strike 110.0
print("\n\nDirect database query for 18JUL25 PUT 110.0:")
cursor.execute("""
    SELECT sr.id, sr.instrument_key, sr.expiry_date, sr.instrument_type, sr.strike,
           json_extract(sr.raw_data, '$.bid') as bid,
           json_extract(sr.raw_data, '$.ask') as ask,
           sc.delta_F, sc.calculation_status
    FROM spot_risk_raw sr
    LEFT JOIN spot_risk_calculated sc ON sr.id = sc.raw_id
    WHERE sr.session_id = 4
      AND sr.expiry_date = '18JUL25'
      AND sr.instrument_type = 'PUT'
      AND sr.strike = 110.0
""")

results = cursor.fetchall()
print(f"Found {len(results)} matches")
for row in results:
    print(f"  ID: {row[0]}, Key: {row[1]}, Expiry: {row[2]}, Type: {row[3]}, Strike: {row[4]}")
    print(f"  Bid: {row[5]}, Ask: {row[6]}, Delta_F: {row[7]}, Status: {row[8]}")

# Check what strikes are available for 18JUL25
print("\n\nAll strikes for 18JUL25:")
cursor.execute("""
    SELECT DISTINCT strike 
    FROM spot_risk_raw 
    WHERE session_id = 4 
      AND expiry_date = '18JUL25'
      AND instrument_type = 'PUT'
    ORDER BY strike
""")

strikes = [row[0] for row in cursor.fetchall()]
print(f"Available strikes: {strikes}")

conn.close()
builder.close() 