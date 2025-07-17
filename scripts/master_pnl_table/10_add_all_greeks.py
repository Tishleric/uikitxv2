#!/usr/bin/env python3
"""
Add all Greek columns to FULLPNL table using spot_risk SQLite database.
Greeks to add: delta_y, gamma_f, gamma_y, speed_f, theta_f, vega_f, vega_y
Note: speed_y and theta_y don't exist in the database
"""
import sqlite3
from pathlib import Path
from datetime import datetime

# Define all Greek columns to add (only those that exist in database)
GREEK_COLUMNS = [
    ('delta_y', 'delta_y', 'Delta w.r.t yield'),
    ('gamma_f', 'gamma_F', 'Gamma w.r.t futures'),  # Note: database uses gamma_F
    ('gamma_y', 'gamma_y', 'Gamma w.r.t yield'),
    ('speed_f', 'speed_F', 'Speed w.r.t futures'),  # Note: database uses speed_F
    # ('speed_y', 'speed_y', 'Speed w.r.t yield'),  # Does not exist in database
    ('theta_f', 'theta_F', 'Theta w.r.t futures'),  # Note: database uses theta_F
    # ('theta_y', 'theta_y', 'Theta w.r.t yield'),  # Does not exist in database
    ('vega_f', 'vega_price', 'Vega in price terms'),  # Note: database uses vega_price
    ('vega_y', 'vega_y', 'Vega w.r.t yield')
]

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

def add_all_greeks():
    """Add all Greek columns to FULLPNL table using spot_risk SQLite database."""
    
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
        # Check existing columns
        cursor.execute("PRAGMA table_info(FULLPNL)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Add columns that don't exist
        columns_added = []
        for col_name, db_field, description in GREEK_COLUMNS:
            if col_name not in existing_columns:
                print(f"Adding {col_name} column ({description})...")
                cursor.execute(f"ALTER TABLE FULLPNL ADD COLUMN {col_name} REAL")
                columns_added.append(col_name)
                print(f"✓ {col_name} column added")
            else:
                print(f"{col_name} column already exists")
        
        if columns_added:
            conn.commit()
            print(f"\nAdded {len(columns_added)} new columns")
        
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
        print(f"\nProcessing {len(symbols)} symbols for all Greeks...")
        
        # Process each symbol
        for (symbol,) in symbols:
            print(f"\nProcessing: {symbol}")
            
            # Parse Bloomberg symbol
            bloomberg_parsed = parse_bloomberg_symbol(symbol)
            if not bloomberg_parsed:
                print(f"  ⚠ Could not parse Bloomberg symbol")
                continue
            
            if bloomberg_parsed['type'] == 'FUTURE':
                # Futures have zero values for all Greeks except delta_f (already set)
                print(f"  Future detected - setting all Greeks to 0")
                update_parts = []
                params = []
                for col_name, _, _ in GREEK_COLUMNS:
                    update_parts.append(f"{col_name} = ?")
                    params.append(0.0)
                
                params.append(symbol)  # WHERE clause
                update_sql = f"UPDATE FULLPNL SET {', '.join(update_parts)} WHERE symbol = ?"
                cursor.execute(update_sql, params)
                
            else:
                # It's an option - look up Greeks in spot risk database
                option_type = bloomberg_parsed['option_type']
                strike = bloomberg_parsed['strike']
                instrument_type = 'PUT' if option_type == 'P' else 'CALL'
                
                # Build query to get all Greeks at once
                greek_fields = [db_field for _, db_field, _ in GREEK_COLUMNS]
                select_fields = ', '.join([f"sc.{field}" for field in greek_fields])
                
                query = f"""
                    SELECT sr.instrument_key, sr.expiry_date, {select_fields}
                    FROM spot_risk.spot_risk_raw sr
                    JOIN spot_risk.spot_risk_calculated sc ON sr.id = sc.raw_id
                    WHERE sr.session_id = ?
                      AND sr.instrument_type = ?
                      AND sr.strike = ?
                      AND sc.calculation_status = 'success'
                    ORDER BY sr.id DESC
                    LIMIT 1
                """
                
                cursor.execute(query, (session_id, instrument_type, strike))
                result = cursor.fetchone()
                
                if result:
                    key, expiry = result[0], result[1]
                    greek_values = result[2:]
                    
                    print(f"  Found in database:")
                    print(f"    Key: {key}")
                    print(f"    Expiry: {expiry}")
                    
                    # Update FULLPNL with all Greeks
                    update_parts = []
                    params = []
                    for i, (col_name, _, description) in enumerate(GREEK_COLUMNS):
                        update_parts.append(f"{col_name} = ?")
                        params.append(greek_values[i])
                        if greek_values[i] is not None:
                            print(f"    {col_name}: {greek_values[i]:.6f}")
                    
                    params.append(symbol)  # WHERE clause
                    update_sql = f"UPDATE FULLPNL SET {', '.join(update_parts)} WHERE symbol = ?"
                    cursor.execute(update_sql, params)
                else:
                    print(f"  ⚠ No data found for {instrument_type} with strike {strike}")
        
        conn.commit()
        
        # Show summary statistics
        print(f"\n{'='*80}")
        print(f"SUMMARY - Greek Columns Population:")
        print(f"{'='*80}")
        
        for col_name, _, description in GREEK_COLUMNS:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({col_name}) as populated,
                    COUNT(CASE WHEN {col_name} != 0 THEN 1 END) as non_zero
                FROM FULLPNL
            """)
            total, populated, non_zero = cursor.fetchone()
            print(f"{col_name:10} ({description:25}): {populated}/{total} populated ({populated/total*100:.1f}%), {non_zero} non-zero")
        
        # Show sample of the complete table
        print(f"\n{'='*80}")
        print("Sample of FULLPNL Table with All Greeks:")
        print(f"{'='*80}")
        
        cursor.execute("""
            SELECT symbol, delta_f, delta_y, gamma_f, vega_f, theta_f
            FROM FULLPNL
            ORDER BY symbol
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<25} {'Delta_F':>10} {'Delta_Y':>10} {'Gamma_F':>10} {'Vega_F':>10} {'Theta_F':>10}")
        print("-" * 85)
        
        # Print data
        for row in results:
            symbol_str = row[0]
            values = row[1:]
            value_strs = [f"{v:.4f}" if v is not None else "NULL" for v in values]
            print(f"{symbol_str:<25} {value_strs[0]:>10} {value_strs[1]:>10} {value_strs[2]:>10} {value_strs[3]:>10} {value_strs[4]:>10}")
        
        # Calculate portfolio-level Greeks
        print(f"\n{'='*80}")
        print("Portfolio-Level Greeks (position-weighted):")
        print(f"{'='*80}")
        
        for col_name, _, description in [('delta_f', 'delta_F', 'Delta w.r.t futures')] + GREEK_COLUMNS:
            cursor.execute(f"""
                SELECT SUM(open_position * {col_name}) as total
                FROM FULLPNL
                WHERE open_position IS NOT NULL AND {col_name} IS NOT NULL
            """)
            
            total = cursor.fetchone()[0]
            if total is not None:
                print(f"{description:30}: {total:>15,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.execute("DETACH DATABASE spot_risk")
        conn.close()

if __name__ == "__main__":
    print("Adding all Greek columns to FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    add_all_greeks() 