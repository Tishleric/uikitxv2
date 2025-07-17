#!/usr/bin/env python3
"""
Add vtexp column to FULLPNL table using spot_risk SQLite database.
vtexp represents time to expiry in years.
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

def add_vtexp_column():
    """Add vtexp column to FULLPNL table using spot_risk SQLite database."""
    
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
        
        if 'vtexp' not in columns:
            print("Adding vtexp column to FULLPNL table...")
            cursor.execute("ALTER TABLE FULLPNL ADD COLUMN vtexp REAL")
            conn.commit()
            print("✓ vtexp column added")
        else:
            print("vtexp column already exists - updating values")
        
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
            
            vtexp = None
            
            if bloomberg_parsed['type'] == 'FUTURE':
                # Futures don't have time to expiry in the same sense
                # Could set to None or 0, depending on business logic
                print(f"  Future detected - skipping vtexp")
                futures_count += 1
                continue
            else:
                # It's an option - look up in spot risk database
                option_type = bloomberg_parsed['option_type']
                strike = bloomberg_parsed['strike']
                instrument_type = 'PUT' if option_type == 'P' else 'CALL'
                
                # Query for vtexp from spot risk database
                # First check if vtexp is in spot_risk_raw
                cursor.execute("""
                    SELECT sr.instrument_key, sr.expiry_date, sr.raw_data
                    FROM spot_risk.spot_risk_raw sr
                    WHERE sr.session_id = ?
                      AND sr.instrument_type = ?
                      AND sr.strike = ?
                    ORDER BY sr.id DESC
                    LIMIT 1
                """, (session_id, instrument_type, strike))
                
                result = cursor.fetchone()
                
                if result:
                    key, expiry, raw_data = result
                    print(f"  Found in database:")
                    print(f"    Key: {key}")
                    print(f"    Expiry: {expiry}")
                    
                    # Parse raw_data JSON to get vtexp
                    import json
                    try:
                        data = json.loads(raw_data)
                        vtexp = data.get('vtexp')
                        if vtexp is not None:
                            print(f"    vtexp: {vtexp}")
                    except:
                        print(f"  ⚠ Could not parse raw_data JSON")
                    
                    # Alternative: check vtexp_mappings table
                    if vtexp is None:
                        cursor.execute("""
                            SELECT vtexp 
                            FROM spot_risk.vtexp_mappings 
                            WHERE session_id = ?
                              AND instrument_type = ?
                              AND ABS(strike - ?) < 0.001
                            LIMIT 1
                        """, (session_id, instrument_type, strike))
                        
                        vtexp_result = cursor.fetchone()
                        if vtexp_result:
                            vtexp = vtexp_result[0]
                            print(f"    vtexp (from mappings): {vtexp}")
                else:
                    print(f"  ⚠ No data found for {instrument_type} with strike {strike}")
                    missing_count += 1
                    continue
            
            # Update FULLPNL with vtexp
            if vtexp is not None:
                cursor.execute("""
                    UPDATE FULLPNL 
                    SET vtexp = ?
                    WHERE symbol = ?
                """, (vtexp, symbol))
                updated_count += 1
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - vtexp Column Population:")
        print(f"{'='*60}")
        print(f"Total symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        print(f"Futures (skipped): {futures_count}")
        print(f"Missing data: {missing_count} ({missing_count/len(symbols)*100:.1f}%)")
        
        # Show final table state
        print(f"\n{'='*60}")
        print("FULLPNL Table with vtexp:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, vtexp, delta_f, open_position
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'vtexp':>10} {'Delta_F':>10} {'Position':>10}")
        print("-" * 70)
        
        # Print data
        for row in results:
            symbol_str, vtexp, delta_f, position = row
            vtexp_str = f"{vtexp:.6f}" if vtexp is not None else "NULL"
            delta_str = f"{delta_f:.4f}" if delta_f is not None else "NULL"
            position_str = f"{position:.0f}" if position is not None else "NULL"
            
            print(f"{symbol_str:<30} {vtexp_str:>10} {delta_str:>10} {position_str:>10}")
        
        # Check the average vtexp for options
        cursor.execute("""
            SELECT AVG(vtexp) as avg_vtexp, MIN(vtexp) as min_vtexp, MAX(vtexp) as max_vtexp
            FROM FULLPNL
            WHERE vtexp IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        if stats[0] is not None:
            print(f"\n{'='*60}")
            print(f"vtexp Statistics (options only):")
            print(f"{'='*60}")
            print(f"Average: {stats[0]:.6f} years")
            print(f"Minimum: {stats[1]:.6f} years")
            print(f"Maximum: {stats[2]:.6f} years")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.execute("DETACH DATABASE spot_risk")
        conn.close()

if __name__ == "__main__":
    print("Adding vtexp column to FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    add_vtexp_column() 