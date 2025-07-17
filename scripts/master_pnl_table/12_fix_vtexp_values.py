#!/usr/bin/env python3
"""
Fix vtexp values in FULLPNL table using vtexp_mappings table.
Maps Bloomberg symbols to vtexp_mappings format to get correct time to expiry values.
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
        type_pos = -1
        for i in range(len(contract_info)-1, -1, -1):
            if contract_info[i] in ['C', 'P']:
                option_type = contract_info[i]
                type_pos = i
                break
        
        # Extract contract code
        # For formats like 3MN5P, the contract is everything before the last digit before P/C
        contract_code = None
        if type_pos > 0:
            # Find where digits start before the option type
            for i in range(type_pos-1, -1, -1):
                if not contract_info[i].isdigit():
                    contract_code = contract_info[:i+1]
                    break
            # If all characters before option type are digits, take the whole prefix
            if contract_code is None:
                contract_code = contract_info[:type_pos]
        
        return {
            'type': 'OPTION',
            'contract_info': contract_info,
            'contract_code': contract_code,
            'strike': strike,
            'option_type': option_type
        }
    
    return None

def map_contract_to_expiry(contract_code):
    """Map Bloomberg contract codes to expiry format for vtexp_mappings."""
    # Known mappings from our data
    mappings = {
        '3MN': '18JUL25',    # 3M series
        '3M': '18JUL25',     # Alternative for 3M series
        'VBYN': '21JUL25',   # VBY series  
        'TYWN': '23JUL25',   # TWN series
    }
    
    # Check each mapping
    for prefix, expiry in mappings.items():
        if contract_code and contract_code.startswith(prefix):
            return expiry
            
    return None

def fix_vtexp_values():
    """Fix vtexp values in FULLPNL table using vtexp_mappings."""
    
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
        # First, let's see what's in vtexp_mappings
        print("Checking vtexp_mappings table...")
        cursor.execute("""
            SELECT symbol, vtexp 
            FROM spot_risk.vtexp_mappings
            ORDER BY symbol
        """)
        
        vtexp_map = {}
        for symbol, vtexp in cursor.fetchall():
            vtexp_map[symbol] = vtexp
            print(f"  {symbol}: {vtexp}")
        
        print(f"\nFound {len(vtexp_map)} entries in vtexp_mappings")
        
        # Get all option symbols from FULLPNL
        cursor.execute("""
            SELECT symbol, vtexp 
            FROM FULLPNL 
            WHERE symbol NOT LIKE 'TYU5%'  -- Exclude futures
            ORDER BY symbol
        """)
        
        symbols = cursor.fetchall()
        print(f"\nProcessing {len(symbols)} option symbols...")
        
        updated_count = 0
        
        for symbol, current_vtexp in symbols:
            print(f"\nProcessing: {symbol}")
            print(f"  Current vtexp: {current_vtexp}")
            
            # Parse Bloomberg symbol
            parsed = parse_bloomberg_symbol(symbol)
            if not parsed or parsed['type'] != 'OPTION':
                print(f"  ⚠ Could not parse as option")
                continue
            
            print(f"  Parsed: contract_code='{parsed['contract_code']}', type={parsed['option_type']}")
            
            # Get expiry from contract code
            expiry = map_contract_to_expiry(parsed['contract_code'])
            if not expiry:
                print(f"  ⚠ Could not map contract code: {parsed['contract_code']}")
                continue
            
            print(f"  Contract code: {parsed['contract_code']} → Expiry: {expiry}")
            
            # Try different symbol formats in vtexp_mappings
            # Format 1: XCME.ZN2.18JUL25
            lookup_key1 = f"XCME.ZN2.{expiry}"
            # Format 2: XCME.ZN.JUL25
            month_year = expiry[2:]  # e.g., "JUL25" from "18JUL25"
            lookup_key2 = f"XCME.ZN.{month_year}"
            
            new_vtexp = None
            used_key = None
            
            if lookup_key1 in vtexp_map:
                new_vtexp = vtexp_map[lookup_key1]
                used_key = lookup_key1
            elif lookup_key2 in vtexp_map:
                new_vtexp = vtexp_map[lookup_key2]
                used_key = lookup_key2
            else:
                # Try finding any entry with the same month/year
                for key, value in vtexp_map.items():
                    if month_year in key:
                        new_vtexp = value
                        used_key = key
                        break
            
            if new_vtexp is not None:
                print(f"  Found in vtexp_mappings: {used_key} → {new_vtexp}")
                
                # Update FULLPNL
                cursor.execute("""
                    UPDATE FULLPNL 
                    SET vtexp = ?
                    WHERE symbol = ?
                """, (new_vtexp, symbol))
                updated_count += 1
                print(f"  ✓ Updated vtexp: {current_vtexp} → {new_vtexp}")
            else:
                print(f"  ⚠ No vtexp mapping found")
        
        conn.commit()
        
        # Show summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - vtexp Values Fixed:")
        print(f"{'='*60}")
        print(f"Total option symbols: {len(symbols)}")
        print(f"Successfully updated: {updated_count} ({updated_count/len(symbols)*100:.1f}%)")
        
        # Show final state
        print(f"\n{'='*60}")
        print("Updated vtexp values in FULLPNL:")
        print(f"{'='*60}")
        
        cursor.execute("""
            SELECT symbol, vtexp, delta_f
            FROM FULLPNL
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        
        # Print header
        print(f"{'Symbol':<30} {'vtexp':>12} {'Delta_F':>10}")
        print("-" * 55)
        
        # Print data
        for row in results:
            symbol_str, vtexp, delta_f = row
            vtexp_str = f"{vtexp:.6f}" if vtexp is not None else "NULL"
            delta_str = f"{delta_f:.4f}" if delta_f is not None else "NULL"
            
            print(f"{symbol_str:<30} {vtexp_str:>12} {delta_str:>10}")
        
        # Show statistics
        cursor.execute("""
            SELECT 
                AVG(vtexp) as avg_vtexp, 
                MIN(vtexp) as min_vtexp, 
                MAX(vtexp) as max_vtexp,
                COUNT(DISTINCT vtexp) as unique_values
            FROM FULLPNL
            WHERE vtexp IS NOT NULL
              AND symbol NOT LIKE 'TYU5%'  -- Exclude futures
        """)
        
        stats = cursor.fetchone()
        if stats[0] is not None:
            print(f"\n{'='*60}")
            print(f"vtexp Statistics (options only):")
            print(f"{'='*60}")
            print(f"Average: {stats[0]:.6f} years")
            print(f"Minimum: {stats[1]:.6f} years") 
            print(f"Maximum: {stats[2]:.6f} years")
            print(f"Unique values: {stats[3]}")
            
            # Convert to days for readability
            print(f"\nIn days:")
            print(f"Average: {stats[0]*365:.1f} days")
            print(f"Minimum: {stats[1]*365:.1f} days") 
            print(f"Maximum: {stats[2]*365:.1f} days")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.execute("DETACH DATABASE spot_risk")
        conn.close()

if __name__ == "__main__":
    print("Fixing vtexp values in FULLPNL table...")
    print(f"Timestamp: {datetime.now()}")
    fix_vtexp_values() 