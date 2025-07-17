#!/usr/bin/env python
"""Check the results of database repopulation."""

import sqlite3
from pathlib import Path

def check_database(db_path, table_queries):
    """Check database contents."""
    if not Path(db_path).exists():
        print(f"  Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for table, query in table_queries.items():
        try:
            cursor.execute(query)
            result = cursor.fetchone()[0]
            print(f"  {table}: {result}")
        except Exception as e:
            print(f"  {table}: Error - {e}")
    
    conn.close()

print("=== P&L Database ===")
check_database("data/output/pnl/pnl_tracker.db", {
    "Positions": "SELECT COUNT(*) FROM positions",
    "CTO Trades": "SELECT COUNT(*) FROM cto_trades",
    "Positions with closed_quantity": "SELECT COUNT(*) FROM positions WHERE closed_quantity > 0"
})

print("\n=== Spot Risk Database ===")
check_database("data/output/spot_risk/spot_risk.db", {
    "Sessions": "SELECT COUNT(*) FROM spot_risk_sessions",
    "Raw records": "SELECT COUNT(*) FROM spot_risk_raw",
    "Raw with Bloomberg symbols": "SELECT COUNT(*) FROM spot_risk_raw WHERE bloomberg_symbol IS NOT NULL",
    "Calculated Greeks": "SELECT COUNT(*) FROM spot_risk_calculated",
    "Successful Greeks": "SELECT COUNT(*) FROM spot_risk_calculated WHERE calculation_status = 'success'"
})

print("\n=== Market Prices Database ===")
check_database("data/output/market_prices/market_prices.db", {
    "Futures prices": "SELECT COUNT(*) FROM futures_prices",
    "Options prices": "SELECT COUNT(*) FROM options_prices"
})

# Check symbol translation issues
print("\n=== Symbol Translation Check ===")
db_path = "data/output/spot_risk/spot_risk.db"
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get sample of untranslated symbols
    cursor.execute("""
        SELECT instrument_key 
        FROM spot_risk_raw 
        WHERE bloomberg_symbol IS NULL 
        LIMIT 5
    """)
    
    untranslated = cursor.fetchall()
    if untranslated:
        print("Sample untranslated symbols:")
        for symbol in untranslated:
            print(f"  {symbol[0]}")
    
    conn.close() 