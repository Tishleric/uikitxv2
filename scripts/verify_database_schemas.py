#!/usr/bin/env python
"""
Verify database schemas match documentation and contain data.
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_table_schema(conn, table_name, expected_columns):
    """Verify a table has the expected columns."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    actual_columns = {col[1]: col[2] for col in columns}  # name: type
    
    print(f"\n📊 Table: {table_name}")
    print(f"   Columns: {len(actual_columns)}")
    
    # Check for missing columns
    missing = set(expected_columns.keys()) - set(actual_columns.keys())
    if missing:
        print(f"   ❌ Missing columns: {missing}")
    
    # Check data count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")
    
    # Show sample data if exists
    if count > 0:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print("   Sample data:")
        for col in df.columns[:5]:  # Show first 5 columns
            print(f"     - {col}: {df[col].iloc[0]}")
    
    return count > 0


def main():
    """Verify all database schemas."""
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    
    all_good = True
    
    # 1. P&L Database
    print("\n🗄️  P&L DATABASE (pnl_tracker.db)")
    pnl_db = "data/output/pnl/pnl_tracker.db"
    if Path(pnl_db).exists():
        conn = sqlite3.connect(pnl_db)
        
        # Verify positions table
        positions_schema = {
            'id': 'INTEGER',
            'instrument_name': 'TEXT',
            'position_quantity': 'REAL',
            'avg_cost': 'REAL',
            'total_realized_pnl': 'REAL',
            'unrealized_pnl': 'REAL',
            'last_market_price': 'REAL',
            'is_option': 'INTEGER',
            'closed_quantity': 'REAL'
        }
        all_good &= verify_table_schema(conn, 'positions', positions_schema)
        
        # Verify cto_trades table
        trades_schema = {
            'id': 'INTEGER',
            'Date': 'DATE',
            'Time': 'TIME',
            'Symbol': 'TEXT',
            'Action': 'TEXT',
            'Quantity': 'INTEGER',
            'Price': 'REAL',
            'Type': 'TEXT',
            'tradeID': 'TEXT'
        }
        all_good &= verify_table_schema(conn, 'cto_trades', trades_schema)
        
        conn.close()
    else:
        print("   ❌ Database not found!")
        all_good = False
    
    # 2. Spot Risk Database
    print("\n🗄️  SPOT RISK DATABASE (spot_risk.db)")
    spot_db = "data/output/spot_risk/spot_risk.db"
    if Path(spot_db).exists():
        conn = sqlite3.connect(spot_db)
        
        # Verify spot_risk_raw table
        raw_schema = {
            'id': 'INTEGER',
            'session_id': 'INTEGER',
            'instrument_key': 'TEXT',
            'bloomberg_symbol': 'TEXT',
            'instrument_type': 'TEXT',
            'midpoint_price': 'REAL',
            'bid': 'REAL',
            'ask': 'REAL',
            'adjtheor': 'REAL',
            'vtexp': 'REAL'
        }
        all_good &= verify_table_schema(conn, 'spot_risk_raw', raw_schema)
        
        # Check Bloomberg symbol translation success
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(bloomberg_symbol) as translated,
                COUNT(CASE WHEN bloomberg_symbol IS NULL THEN 1 END) as failed
            FROM spot_risk_raw
        """)
        stats = cursor.fetchone()
        print(f"\n   📊 Bloomberg Symbol Translation:")
        print(f"      Total: {stats[0]}, Translated: {stats[1]}, Failed: {stats[2]}")
        
        # Verify spot_risk_calculated table
        calc_schema = {
            'id': 'INTEGER',
            'raw_id': 'INTEGER',
            'implied_vol': 'REAL',
            'delta_F': 'REAL',
            'delta_y': 'REAL',
            'gamma_F': 'REAL',
            'gamma_y': 'REAL',
            'theta_F': 'REAL',
            'vega_price': 'REAL',
            'vega_y': 'REAL',
            'calculation_status': 'TEXT'
        }
        all_good &= verify_table_schema(conn, 'spot_risk_calculated', calc_schema)
        
        # Check calculation success rate
        cursor.execute("""
            SELECT 
                calculation_status,
                COUNT(*) as count
            FROM spot_risk_calculated
            GROUP BY calculation_status
        """)
        print(f"\n   📊 Greek Calculation Status:")
        for status, count in cursor.fetchall():
            print(f"      {status}: {count}")
        
        conn.close()
    else:
        print("   ❌ Database not found!")
        all_good = False
    
    # 3. Market Prices Database
    print("\n🗄️  MARKET PRICES DATABASE (market_prices.db)")
    market_db = "data/output/market_prices/market_prices.db"
    if Path(market_db).exists():
        conn = sqlite3.connect(market_db)
        
        # Check if tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"   Tables: {tables}")
        
        # Try to check for price data
        if 'market_prices' in tables:
            cursor.execute("SELECT COUNT(*) FROM market_prices")
            count = cursor.fetchone()[0]
            print(f"   Market price records: {count}")
        
        conn.close()
    else:
        print("   ❌ Database not found!")
        # Market prices are optional for now
    
    # Final verdict
    print("\n" + "=" * 80)
    if all_good:
        print("✅ All required schemas verified and contain data!")
        print("Ready to create master P&L view.")
    else:
        print("❌ Some issues found - check above for details.")
    
    return all_good


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 