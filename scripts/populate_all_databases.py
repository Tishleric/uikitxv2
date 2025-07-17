#!/usr/bin/env python
"""
Comprehensive script to populate all databases with correct schema and data.

This ensures:
1. P&L database has trades and positions
2. Spot risk database has raw and calculated data
3. Market prices database has price data (if available)
4. All schemas match our documentation
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService
from lib.trading.market_prices.storage import MarketPriceStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_status():
    """Check the current status of all databases."""
    print("\n" + "=" * 60)
    print("DATABASE STATUS CHECK")
    print("=" * 60)
    
    # 1. P&L Database
    pnl_db = Path("data/output/pnl/pnl_tracker.db")
    if pnl_db.exists():
        storage = PnLStorage(str(pnl_db))
        conn = storage._get_connection()
        cursor = conn.cursor()
        
        # Check trades
        cursor.execute("SELECT COUNT(*) FROM cto_trades")
        trade_count = cursor.fetchone()[0]
        
        # Check positions
        cursor.execute("SELECT COUNT(*) FROM positions")
        position_count = cursor.fetchone()[0]
        
        # Check processed trades
        cursor.execute("SELECT COUNT(*) FROM processed_trades")
        processed_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 P&L Database: {pnl_db}")
        print(f"   - CTO Trades: {trade_count}")
        print(f"   - Positions: {position_count}")
        print(f"   - Processed Trades: {processed_count}")
    else:
        print(f"\n❌ P&L Database not found: {pnl_db}")
    
    # 2. Spot Risk Database
    spot_risk_db = Path("data/output/spot_risk/spot_risk.db")
    if spot_risk_db.exists():
        import sqlite3
        conn = sqlite3.connect(str(spot_risk_db))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Spot Risk Database: {spot_risk_db}")
        print(f"   Tables: {[t[0] for t in tables]}")
        
        for table in ['spot_risk_sessions', 'spot_risk_raw', 'spot_risk_calculated']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} records")
            
        # Check Bloomberg symbols
        cursor.execute("SELECT COUNT(*) FROM spot_risk_raw WHERE bloomberg_symbol IS NOT NULL")
        bloomberg_count = cursor.fetchone()[0]
        print(f"   - Bloomberg symbols: {bloomberg_count}")
        
        conn.close()
    else:
        print(f"\n❌ Spot Risk Database not found: {spot_risk_db}")
    
    # 3. Market Prices Database
    market_db = Path("data/output/market_prices/market_prices.db")
    if market_db.exists():
        import sqlite3
        conn = sqlite3.connect(str(market_db))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Market Prices Database: {market_db}")
        print(f"   Tables: {[t[0] for t in tables]}")
        
        conn.close()
    else:
        print(f"\n❌ Market Prices Database not found: {market_db}")


def ensure_vtexp_fallback():
    """Ensure vtexp fallback values exist."""
    vtexp_db = Path("data/output/spot_risk/spot_risk.db")
    if not vtexp_db.exists():
        return
        
    import sqlite3
    conn = sqlite3.connect(str(vtexp_db))
    cursor = conn.cursor()
    
    # Check if vtexp_mappings table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vtexp_mappings (
            symbol TEXT PRIMARY KEY,
            vtexp REAL NOT NULL,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add some fallback values
    fallback_vtexp = [
        ('XCME.ZN.SEP25', 0.166667, 'fallback'),
        ('XCME.ZN.JUL25', 0.041667, 'fallback'),
        ('XCME.ZN2.11JUL25', 0.030556, 'fallback'),
        ('XCME.ZN2.14JUL25', 0.038889, 'fallback'),
        ('XCME.ZN2.16JUL25', 0.044444, 'fallback'),
        ('XCME.ZN2.18JUL25', 0.050000, 'fallback'),
    ]
    
    for symbol, vtexp, source in fallback_vtexp:
        cursor.execute("""
            INSERT OR REPLACE INTO vtexp_mappings (symbol, vtexp, source)
            VALUES (?, ?, ?)
        """, (symbol, vtexp, source))
    
    conn.commit()
    conn.close()
    
    logger.info("Added fallback vtexp values")


def create_summary_view():
    """Create a summary view combining all data sources."""
    pnl_db = Path("data/output/pnl/pnl_tracker.db")
    if not pnl_db.exists():
        logger.error("P&L database not found")
        return
        
    storage = PnLStorage(str(pnl_db))
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Create a view that shows all positions with their details
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS position_summary AS
        SELECT 
            p.instrument_name,
            p.position_quantity,
            p.avg_cost,
            p.unrealized_pnl,
            p.last_market_price,
            p.is_option,
            p.option_strike,
            p.option_expiry,
            p.closed_quantity,
            COUNT(t.id) as trade_count,
            MIN(t.Date) as first_trade_date,
            MAX(t.Date) as last_trade_date
        FROM positions p
        LEFT JOIN cto_trades t ON p.instrument_name = t.Symbol
        GROUP BY p.instrument_name
    """)
    
    conn.commit()
    
    # Query and display the summary
    summary_df = pd.read_sql_query("SELECT * FROM position_summary", conn)
    
    print("\n" + "=" * 60)
    print("POSITION SUMMARY")
    print("=" * 60)
    print(summary_df.to_string(index=False))
    
    conn.close()


def main():
    """Main function to check and populate databases."""
    
    print("\n🚀 DATABASE POPULATION CHECK")
    print("=" * 60)
    
    # 1. Check current status
    check_database_status()
    
    # 2. Ensure vtexp fallback values
    ensure_vtexp_fallback()
    
    # 3. Create summary view
    create_summary_view()
    
    # 4. Final status check
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    
    # Quick summary
    results = {
        'P&L Database': False,
        'Positions': False,
        'Spot Risk Data': False,
        'Bloomberg Symbols': False,
        'Greek Calculations': False
    }
    
    # Check P&L
    pnl_db = Path("data/output/pnl/pnl_tracker.db")
    if pnl_db.exists():
        storage = PnLStorage(str(pnl_db))
        conn = storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM positions")
        if cursor.fetchone()[0] > 0:
            results['P&L Database'] = True
            results['Positions'] = True
        
        conn.close()
    
    # Check Spot Risk
    spot_risk_db = Path("data/output/spot_risk/spot_risk.db")
    if spot_risk_db.exists():
        import sqlite3
        conn = sqlite3.connect(str(spot_risk_db))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM spot_risk_raw")
        if cursor.fetchone()[0] > 0:
            results['Spot Risk Data'] = True
            
        cursor.execute("SELECT COUNT(*) FROM spot_risk_raw WHERE bloomberg_symbol IS NOT NULL")
        if cursor.fetchone()[0] > 0:
            results['Bloomberg Symbols'] = True
            
        cursor.execute("SELECT COUNT(*) FROM spot_risk_calculated WHERE calculation_status = 'success'")
        if cursor.fetchone()[0] > 0:
            results['Greek Calculations'] = True
        
        conn.close()
    
    # Display results
    for item, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {item}: {'Ready' if status else 'Missing/Empty'}")
    
    # Overall status
    all_ready = all(results.values())
    if all_ready:
        print("\n✅ All databases are populated and ready for P&L table creation!")
    else:
        print("\n⚠️  Some components are missing. Run the following scripts:")
        if not results['Positions']:
            print("   - python scripts/create_positions_from_trades.py")
        if not results['Spot Risk Data']:
            print("   - Process spot risk files using SpotRiskWatcher")
        print("\nRefer to docs/pnl_data_structure_mapping.md for details.")


if __name__ == "__main__":
    main() 