#!/usr/bin/env python3
"""
Debug FULLPNL issues:
1. TYU5 missing price data
2. TYU5 gamma_f = 0.004202 (should be 0 for futures)
3. Missing Y-space Greeks for options
"""
import sqlite3
import os
from pathlib import Path

def investigate_fullpnl():
    """Investigate FULLPNL issues."""
    db_path = Path("data/output/pnl/pnl_tracker.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*80)
    print("FULLPNL ISSUES INVESTIGATION")
    print("="*80)
    
    # 1. Check TYU5 data
    print("\n1. TYU5 Futures Data:")
    print("-"*60)
    cursor.execute("""
        SELECT symbol, bid, ask, price, px_last, px_settle, 
               delta_f, gamma_f, gamma_y, vega_f, vega_y
        FROM FULLPNL 
        WHERE symbol = 'TYU5 Comdty'
    """)
    row = cursor.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key}: {row[key]}")
    
    # 2. Check market prices for TYU5
    print("\n2. Market Prices Database Check:")
    print("-"*60)
    mp_db = Path("data/output/market_prices/market_prices.db")
    if mp_db.exists():
        mp_conn = sqlite3.connect(mp_db)
        mp_cursor = mp_conn.cursor()
        
        # Check futures prices
        mp_cursor.execute("""
            SELECT symbol, Flash_Close, prior_close, trade_date
            FROM futures_prices
            WHERE symbol = 'TYU5'
            ORDER BY trade_date DESC
            LIMIT 5
        """)
        print("  Futures prices for TYU5:")
        for row in mp_cursor.fetchall():
            print(f"    {row}")
        mp_conn.close()
    
    # 3. Check spot risk data
    print("\n3. Spot Risk Database Check:")
    print("-"*60)
    sr_db = Path("data/output/spot_risk/spot_risk.db")
    if sr_db.exists():
        sr_conn = sqlite3.connect(sr_db)
        sr_cursor = sr_conn.cursor()
        
        # Check for TYU5 in spot risk
        sr_cursor.execute("""
            SELECT instrument_key, 
                   json_extract(raw_data, '$.bid') as bid,
                   json_extract(raw_data, '$.ask') as ask,
                   json_extract(raw_data, '$.adjtheor') as adjtheor
            FROM spot_risk_raw
            WHERE instrument_key LIKE '%SEP25%'
            ORDER BY id DESC
            LIMIT 5
        """)
        print("  Spot risk data for SEP25 futures:")
        for row in sr_cursor.fetchall():
            print(f"    {row}")
        sr_conn.close()
    
    # 4. Check Y-space Greeks for options
    print("\n4. Y-space Greeks for Options:")
    print("-"*60)
    cursor.execute("""
        SELECT symbol, delta_f, delta_y, gamma_f, gamma_y, vega_f, vega_y
        FROM FULLPNL
        WHERE symbol LIKE '%P%' OR symbol LIKE '%C%'
        ORDER BY symbol
    """)
    
    print("  Symbol                         delta_f  delta_y  gamma_f  gamma_y  vega_f  vega_y")
    print("  " + "-"*78)
    for row in cursor.fetchall():
        print(f"  {row['symbol']:<30} {row['delta_f'] or 'None':>7} {row['delta_y'] or 'None':>7} "
              f"{row['gamma_f'] or 'None':>7} {row['gamma_y'] or 'None':>7} "
              f"{row['vega_f'] or 'None':>7} {row['vega_y'] or 'None':>7}")
    
    # 5. Check FULLPNL schema
    print("\n5. FULLPNL Table Schema:")
    print("-"*60)
    cursor.execute("PRAGMA table_info(FULLPNL)")
    y_space_columns = []
    for col in cursor.fetchall():
        if '_y' in col[1]:
            y_space_columns.append(col[1])
    print(f"  Y-space columns found: {y_space_columns}")
    
    # 6. Check builder code for hardcoded values
    print("\n6. Checking for hardcoded gamma in builder...")
    print("-"*60)
    builder_path = Path("lib/trading/fullpnl/builder.py")
    if builder_path.exists():
        with open(builder_path, 'r') as f:
            content = f.read()
            if '0.004202' in content:
                print("  ⚠️ Found hardcoded 0.004202 in builder.py!")
            if 'gamma_f = 0' in content or "'gamma_f': 0" in content:
                print("  ✓ Found gamma_f = 0 assignment for futures")
            else:
                print("  ❌ No gamma_f = 0 assignment found for futures")
    
    conn.close()

if __name__ == "__main__":
    investigate_fullpnl() 