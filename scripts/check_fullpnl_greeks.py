#!/usr/bin/env python3
"""Check which symbols have Greeks populated."""

import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
conn = sqlite3.connect(project_root / "data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT symbol, delta_f, gamma_f, vega_f, bid, ask
    FROM FULLPNL 
    ORDER BY symbol
""")

print("FULLPNL Greek Coverage:")
print("=" * 80)
print(f"{'Symbol':<30} {'Delta_F':>10} {'Gamma_F':>10} {'Vega_F':>10} {'Bid':>10} {'Ask':>10}")
print("-" * 80)

for row in cursor.fetchall():
    symbol, delta_f, gamma_f, vega_f, bid, ask = row
    delta_str = f"{delta_f:.4f}" if delta_f is not None else "NULL"
    gamma_str = f"{gamma_f:.4f}" if gamma_f is not None else "NULL"
    vega_str = f"{vega_f:.4f}" if vega_f is not None else "NULL"
    bid_str = f"{bid:.6f}" if bid is not None else "NULL"
    ask_str = f"{ask:.6f}" if ask is not None else "NULL"
    
    print(f"{symbol:<30} {delta_str:>10} {gamma_str:>10} {vega_str:>10} {bid_str:>10} {ask_str:>10}")

# Summary
cursor.execute("""
    SELECT 
        COUNT(CASE WHEN delta_f IS NOT NULL THEN 1 END) as with_delta,
        COUNT(CASE WHEN gamma_f IS NOT NULL THEN 1 END) as with_gamma,
        COUNT(CASE WHEN vega_f IS NOT NULL THEN 1 END) as with_vega,
        COUNT(CASE WHEN bid IS NOT NULL THEN 1 END) as with_bid,
        COUNT(CASE WHEN ask IS NOT NULL THEN 1 END) as with_ask,
        COUNT(*) as total
    FROM FULLPNL
""")

stats = cursor.fetchone()
total = stats[5]
print("\nSummary:")
print(f"  Total symbols: {total}")
print(f"  With delta_f: {stats[0]} ({stats[0]/total*100:.1f}%)")
print(f"  With gamma_f: {stats[1]} ({stats[1]/total*100:.1f}%)")
print(f"  With vega_f: {stats[2]} ({stats[2]/total*100:.1f}%)")
print(f"  With bid: {stats[3]} ({stats[3]/total*100:.1f}%)")
print(f"  With ask: {stats[4]} ({stats[4]/total*100:.1f}%)")

# Show which strikes we're missing
print("\nMissing Greeks for:")
cursor.execute("""
    SELECT symbol 
    FROM FULLPNL 
    WHERE delta_f IS NULL 
    AND symbol NOT LIKE 'TYU5%'
    ORDER BY symbol
""")

for (symbol,) in cursor.fetchall():
    parts = symbol.replace(' Comdty', '').split()
    if len(parts) == 2:
        strike = float(parts[1])
        print(f"  {symbol} (strike: {strike})")

conn.close() 