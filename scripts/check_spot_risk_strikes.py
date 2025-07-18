#!/usr/bin/env python3
"""Check what strikes are available in spot risk database."""

import sys
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

db_path = project_root / "data/output/spot_risk/spot_risk.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get latest session
cursor.execute("""
    SELECT session_id, source_file, data_timestamp
    FROM spot_risk_sessions 
    ORDER BY start_time DESC 
    LIMIT 1
""")
session_info = cursor.fetchone()
print(f"Latest session: {session_info[0]}")
print(f"Source file: {session_info[1]}")
print(f"Data timestamp: {session_info[2]}")
print()

# Get all strikes from spot risk
cursor.execute("""
    SELECT DISTINCT instrument_type, strike, COUNT(*) as count
    FROM spot_risk_raw
    WHERE session_id = ?
      AND instrument_type IN ('PUT', 'CALL')
    GROUP BY instrument_type, strike
    ORDER BY strike, instrument_type
""", (session_info[0],))

results = cursor.fetchall()
print("Available strikes in spot risk database:")
print("=" * 50)
print(f"{'Type':<6} {'Strike':>10} {'Count':>6}")
print("-" * 50)

for itype, strike, count in results:
    print(f"{itype:<6} {strike:>10.3f} {count:>6}")
    
# Show our missing strikes
print("\nOur FULLPNL strikes:")
print("-" * 50)

cursor.close()
conn = sqlite3.connect(project_root / "data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT symbol 
    FROM FULLPNL 
    WHERE symbol LIKE '%P %' OR symbol LIKE '%C %'
    ORDER BY symbol
""")

for (symbol,) in cursor.fetchall():
    # Parse strike
    parts = symbol.replace(' Comdty', '').split()
    if len(parts) == 2:
        strike = float(parts[1])
        option_type = 'PUT' if 'P' in parts[0] else 'CALL'
        print(f"{symbol:<35} Strike: {strike:.3f} ({option_type})")

conn.close() 