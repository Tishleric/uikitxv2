#!/usr/bin/env python3
"""Debug spot risk update issue."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.fullpnl import FULLPNLBuilder
import traceback

# Initialize builder
builder = FULLPNLBuilder()

print("Testing spot risk update...")
print("=" * 50)

try:
    # Get all symbols
    cursor = builder.pnl_db.execute("SELECT symbol FROM FULLPNL")
    symbols = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(symbols)} symbols in FULLPNL")
    
    # Test spot risk data retrieval
    print("\nTesting spot risk data retrieval...")
    spot_risk_data = builder.spot_risk_db.get_latest_spot_risk_data(symbols)
    print(f"Retrieved data for {len(spot_risk_data)} symbols")
    
    # Show what we got
    for symbol, data in spot_risk_data.items():
        print(f"\n{symbol}:")
        print(f"  bid: {data.get('bid')}")
        print(f"  ask: {data.get('ask')}")
        print(f"  delta_F: {data.get('delta_F')}")
        
    # Now try the update
    print("\n\nRunning update_spot_risk_data()...")
    results = builder.update_spot_risk_data()
    print(f"Results: {results}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()
    
finally:
    builder.close()
    print("\nDone!") 