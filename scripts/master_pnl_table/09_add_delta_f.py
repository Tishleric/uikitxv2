#!/usr/bin/env python3
"""
Add delta_f column to FULLPNL table using spot_risk SQLite database.
This version uses the database instead of CSV files for better data quality.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def parse_bloomberg_symbol(symbol):
    """Parse Bloomberg option symbol to extract components."""
    # Remove " Comdty" suffix
    symbol = symbol.replace(" Comdty", "")
    
    # Check if it's a future (no strike price)
    parts = symbol.split()
    if len(parts) == 1:
        return {'type': 'FUTURE', 'symbol': parts[0]}
    
    # It's an option - parse components
    if len(parts) == 2:
        contract_info = parts[0]
        strike = float(parts[1])
        
        # Extract option type (last character before any digits)
        option_type = None
        for i in range(len(contract_info)-1, -1, -1):
            if contract_info[i] in ['C', 'P']:
                option_type = contract_info[i]
                break
        
        return {
            'type': 'OPTION',
            'contract_info': contract_info,
            'strike': strike,
            'option_type': option_type
        }
    
    return None

def add_delta_f_column_sqlite():
    """Add delta_f column to FULLPNL table using spot_risk SQLite database."""
    
    # Database paths
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    spot_risk_db_path = project_root / "data/output/spot_risk/spot_risk.db"
    
    if not pnl_db_path.exists():
        print(f"Error: P&L database not found at {pnl_db_path}")
        return
        
    if not spot_risk_db_path.exists():
        print(f"Error: Spot risk database not found at {spot_risk_db_path}")
        return
    
    # Connect to P&L database
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    # Attach spot risk database
    cursor.execute(f"ATTACH DATABASE '{spot_risk_db_path}' AS spot_risk")
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(FULLPNL)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'delta_f' not in columns:
            print("Adding delta_f column to FULLPNL table...")
            cursor.execute("ALTER TABLE FULLPNL ADD COLUMN delta_f REAL")
            conn.commit()
            print("✓ delta_f column added")
        else:
            print("delta_f column already exists - updating values")
        
        # Get latest session from spot_risk
        cursor.execute("""
            SELECT session_id, source_file, data_timestamp 
            FROM spot_risk.spot_risk_sessions 
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        
        session_info = cursor.fetchone()
        if not session_info:
            print("Error: No spot risk sessions found")
            return
            
        session_id, source_file, data_timestamp = session_info
        print(f"\nUsing spot risk session {session_id}")
        print(f"Source: {source_file}")
        print(f"Data timestamp: {data_timestamp}")
        
        # Get all symbols from FULLPNL
        cursor.execute("SELECT symbol FROM FULLPNL")
        symbols = cursor.fetchall()
        print(f"\nProcessing {len(symbols)} symbols...")
        
        updated_count = 0
        missing_count = 0
        futures_count = 0
        
        for (symbol,) in symbols:
            print(f"\nProcessing: {symbol}")
            
            # Parse Bloomberg symbol
            bloomberg_parsed = parse_bloomberg_symbol(symbol)
            if not bloomberg_parsed:
                print(f"  ⚠ Could not parse Bloomberg symbol")
                missing_count += 1
                continue
            
            delta_f = None
            
            if bloomberg_parsed['type'] == 'FUTURE':
                # Futures have hardcoded delta of 63
                delta_f = 63.0
                print(f"  Future detected - using hardcoded delta_f = {delta_f}")
                futures_count += 1
            else:
                # It's an option - look up in spot risk database
                option_type = bloomberg_parsed['option_type']
                strike = bloomberg_parsed['strike']
                instrument_type = 'PUT' if option_type == 'P' else 'CALL'
                
                # Query for delta_F from spot risk database
                cursor.execute("""
                    SELECT sr.instrument_key, sr.expiry_date, sc.delta_F, sc.calculation_status
                    FROM spot_risk.spot_risk_raw sr
                    JOIN spot_risk.spot_risk_calculated sc ON sr.id = sc.raw_id
                    WHERE sr.session_id = ?
                      AND sr.instrument_type = ?
                      AND sr.strike = ?
                      AND sc.calculation_status = 'success'
                      AND sc.delta_F IS NOT NULL
                    ORDER BY sr.id DESC
                    LIMIT 1
                """, (session_id, instrument_type, strike))
                
                result = cursor.fetchone()
                
                if result:
                    key, expiry, delta_f, status = result
                    print(f"  Found in database:")
                    print(f"    Key: {key}")
                    print(f"    Expiry: {expiry}")
                    print(f"    Delta_F: {delta_f}")
                else:
                    print(f"  ⚠ No data found for {instrument_type} with strike {strike}")
                    missing_count += 1
                    continue
            
            # Update FULLPNL with delta_f
            if delta_f is not None:
                cursor.execute("""
                    UPDATE FULLPNL 
                    SET delta_f = ?
                    WHERE symbol = ?
                """, (delta_f, symbol))
                updated_count += 1
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - delta_f Column Population:")
        print(f"{'='*60}")
        print(f"Total symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        print(f"  - Futures (hardcoded): {futures_count}")
        print(f"  - Options (from database): {updated_count - futures_count}")
        print(f"Missing data: {missing_count} ({missing_count/len(symbols)*100:.1f}%)")
        
        # Show final table state
        print(f"\n{'='*60}")
        print("FULLPNL Table with delta_f:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, open_position, delta_f, px_last
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'Position':>10} {'Delta_F':>10} {'px_last':>10}")
        print("-" * 70)
        
        # Print data
        for row in results:
            symbol_str, position, delta_f, px_last = row
            position_str = f"{position:.0f}" if position is not None else "NULL"
            delta_str = f"{delta_f:.4f}" if delta_f is not None else "NULL"
            px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
            
            print(f"{symbol_str:<30} {position_str:>10} {delta_str:>10} {px_last_str:>10}")
        
        # Calculate position-weighted delta
        cursor.execute("""
            SELECT SUM(open_position * delta_f) as total_delta
            FROM FULLPNL
            WHERE open_position IS NOT NULL AND delta_f IS NOT NULL
        """)
        
        total_delta = cursor.fetchone()[0]
        if total_delta:
            print(f"\n{'='*60}")
            print(f"Portfolio Total Delta (position-weighted): {total_delta:,.2f}")
            print(f"{'='*60}")
        
        # Show which symbols are missing data
        cursor.execute("""
            SELECT symbol 
            FROM FULLPNL 
            WHERE delta_f IS NULL
            ORDER BY symbol
        """)
        
        missing_symbols = cursor.fetchall()
        if missing_symbols:
            print(f"\n{'='*60}")
            print("Symbols missing delta_f data:")
            print(f"{'='*60}")
            for (sym,) in missing_symbols:
                # Parse to understand why
                parsed = parse_bloomberg_symbol(sym)
                if parsed and parsed['type'] == 'OPTION':
                    print(f"  {sym} (Strike: {parsed['strike']})")
                else:
                    print(f"  {sym}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.execute("DETACH DATABASE spot_risk")
        conn.close()

if __name__ == "__main__":
    print("Adding delta_f column to FULLPNL table from SQLite database...")
    print(f"Timestamp: {datetime.now()}")
    add_delta_f_column_sqlite() 