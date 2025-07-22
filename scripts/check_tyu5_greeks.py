#!/usr/bin/env python3
"""Check if TYU5 futures has DV01 and Gamma populated in FULLPNL table."""

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')

# Query for TYU5 futures
query = """
SELECT 
    symbol_tyu5,
    type,
    dv01_f,
    gamma_f,
    delta_f,
    theta_f,
    vega_f
FROM FULLPNL 
WHERE symbol_tyu5 = 'TYU5'
"""

# Execute query
result = pd.read_sql_query(query, conn)
conn.close()

# Display results
print("TYU5 Futures Greeks in FULLPNL Table:")
print("=" * 50)

if not result.empty:
    row = result.iloc[0]
    print(f"Symbol: {row['symbol_tyu5']}")
    print(f"Type: {row['type']}")
    print(f"DV01: {row['dv01_f']}")
    print(f"Gamma: {row['gamma_f']}")
    print(f"Delta: {row['delta_f']}")
    print(f"Theta: {row['theta_f']}")
    print(f"Vega: {row['vega_f']}")
    
    # Check if values are populated
    if row['dv01_f'] == 63.0 and row['gamma_f'] == 0.0042:
        print("\n✅ SUCCESS: DV01 and Gamma are correctly populated!")
    else:
        print("\n❌ Issue: DV01 or Gamma values don't match expected values")
        print(f"   Expected: DV01=63.0, Gamma=0.0042")
        print(f"   Actual: DV01={row['dv01_f']}, Gamma={row['gamma_f']}")
else:
    print("No TYU5 futures found in FULLPNL table") 