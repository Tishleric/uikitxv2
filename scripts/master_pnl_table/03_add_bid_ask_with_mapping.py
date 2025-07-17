#!/usr/bin/env python3
"""
03_add_bid_ask_with_mapping.py

Adds bid and ask columns to FULLPNL table by matching Bloomberg symbols 
with Actant format spot risk data based on expiry and strike.
"""

import sqlite3
import os
import pandas as pd
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_bloomberg_symbol(symbol):
    """Parse Bloomberg option symbol to extract components.
    
    Examples:
    - TYU5 Comdty -> {'type': 'FUT', 'contract': 'TY', 'expiry': 'U5'}
    - VBYN25P3 110.250 Comdty -> {'type': 'PUT', 'contract': 'VBY', 'expiry': 'N25', 'strike': 110.25}
    - 3MN5P 110.000 Comdty -> {'type': 'PUT', 'contract': '3M', 'expiry': 'N5', 'strike': 110.0}
    """
    # Remove 'Comdty' suffix
    symbol = symbol.replace(' Comdty', '').strip()
    
    # Check if it's an option (has a strike price)
    parts = symbol.split()
    if len(parts) == 2:
        # Option format
        contract_part = parts[0]
        strike = float(parts[1])
        
        # Extract put/call indicator
        if 'P' in contract_part:
            opt_type = 'PUT'
            # Find where P starts (could be 3MN5P or VBYN25P3)
            p_idx = contract_part.rfind('P')
            base_contract = contract_part[:p_idx]
        elif 'C' in contract_part:
            opt_type = 'CALL'
            c_idx = contract_part.rfind('C')
            base_contract = contract_part[:c_idx]
        else:
            return None
            
        return {
            'type': opt_type,
            'symbol': symbol,
            'strike': strike,
            'contract_code': contract_part,
            'base_contract': base_contract
        }
    else:
        # Future format (e.g., TYU5)
        return {
            'type': 'FUT',
            'symbol': symbol,
            'contract_code': symbol
        }


def parse_actant_key(key):
    """Parse Actant format key to extract components.
    
    Examples:
    - XCME.ZN.SEP25 -> {'type': 'FUT', 'expiry': 'SEP25'}
    - XCME.ZN3.18JUL25.110.C -> {'type': 'CALL', 'expiry': '18JUL25', 'strike': 110.0}
    - XCME.ZN3.18JUL25.110:25.P -> {'type': 'PUT', 'expiry': '18JUL25', 'strike': 110.25}
    """
    parts = key.split('.')
    
    if len(parts) == 3:
        # Future
        return {
            'type': 'FUT',
            'expiry': parts[2],
            'key': key
        }
    elif len(parts) >= 5:
        # Option
        expiry = parts[2]
        strike_str = parts[3]
        opt_type = 'CALL' if parts[-1] == 'C' else 'PUT'
        
        # Handle fractional strikes (110:25 = 110.25)
        if ':' in strike_str:
            main, frac = strike_str.split(':')
            strike = float(main) + float(frac) / 100
        else:
            strike = float(strike_str)
            
        return {
            'type': opt_type,
            'expiry': expiry,
            'strike': strike,
            'key': key
        }
    
    return None


def find_matching_spot_risk_data(csv_path, bloomberg_symbols):
    """Find matching bid/ask data for Bloomberg symbols in spot risk CSV."""
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Parse all Bloomberg symbols
    bloomberg_data = {}
    for symbol in bloomberg_symbols:
        parsed = parse_bloomberg_symbol(symbol)
        if parsed:
            bloomberg_data[symbol] = parsed
    
    # Create mapping
    matches = {}
    
    # Group options by expiry in the CSV
    options_by_expiry = {}
    for _, row in df.iterrows():
        key = row['key']
        if pd.isna(key) or (isinstance(key, str) and key in ['XCME.ZN', 'NET_FUTURES', 'NET_OPTIONS_F', 'NET_OPTIONS_Y']):
            continue
            
        parsed_actant = parse_actant_key(key)
        if parsed_actant and parsed_actant['type'] in ['CALL', 'PUT']:
            expiry = parsed_actant['expiry']
            if expiry not in options_by_expiry:
                options_by_expiry[expiry] = []
            options_by_expiry[expiry].append((row, parsed_actant))
    
    # Match each Bloomberg symbol
    for bloom_symbol, bloom_data in bloomberg_data.items():
        matched = False
        
        # Match futures
        if bloom_data['type'] == 'FUT':
            for _, row in df.iterrows():
                key = row['key']
                if pd.isna(key):
                    continue
                    
                parsed_actant = parse_actant_key(key)
                if parsed_actant and parsed_actant['type'] == 'FUT':
                    # Match TYU5 with SEP25 
                    if 'SEP' in parsed_actant['expiry'] and 'U' in bloom_data['contract_code']:
                        if bloom_symbol not in matches:  # Avoid overwriting
                            matches[bloom_symbol] = {
                                'bid': row['bid'],
                                'ask': row['ask'],
                                'actant_key': key
                            }
                            logger.info(f"Matched future {bloom_symbol} -> {key}")
                            matched = True
                            break
        
        # Match options
        elif bloom_data['type'] in ['CALL', 'PUT'] and 'strike' in bloom_data:
            # Determine likely expiry based on contract code
            contract_code = bloom_data['contract_code']
            
            # Map Bloomberg contract codes to likely expiries
            if '3M' in contract_code:
                likely_expiries = ['18JUL25']  # 3M series -> July 18
            elif 'VBY' in contract_code:
                likely_expiries = ['21JUL25']  # VBY series -> July 21
            elif 'TWN' in contract_code:
                likely_expiries = ['23JUL25']  # TWN series -> July 23
            else:
                likely_expiries = list(options_by_expiry.keys())
            
            # Try to find match in likely expiries
            for expiry in likely_expiries:
                if expiry in options_by_expiry:
                    for row, parsed_actant in options_by_expiry[expiry]:
                        if (bloom_data['type'] == parsed_actant['type'] and
                            abs(bloom_data['strike'] - parsed_actant['strike']) < 0.001):
                            if bloom_symbol not in matches:  # Avoid overwriting
                                matches[bloom_symbol] = {
                                    'bid': row['bid'],
                                    'ask': row['ask'],
                                    'actant_key': row['key']
                                }
                                logger.info(f"Matched {bloom_data['type']} {bloom_symbol} -> {row['key']}")
                                matched = True
                                break
                if matched:
                    break
    
    return matches


def update_fullpnl_with_matches(conn, matches):
    """Update FULLPNL table with matched bid/ask data."""
    cursor = conn.cursor()
    
    updates = 0
    for symbol, data in matches.items():
        bid = data['bid'] if pd.notna(data['bid']) else None
        ask = data['ask'] if pd.notna(data['ask']) else None
        
        cursor.execute("""
            UPDATE FULLPNL 
            SET bid = ?, ask = ?
            WHERE symbol = ?
        """, (bid, ask, symbol))
        
        if cursor.rowcount > 0:
            updates += cursor.rowcount
            logger.debug(f"Updated {symbol}: bid={bid}, ask={ask} (from {data['actant_key']})")
    
    conn.commit()
    logger.info(f"Updated {updates} rows with bid/ask data")
    return updates


def display_results(conn):
    """Display the updated FULLPNL table."""
    cursor = conn.cursor()
    
    print("\nUpdated FULLPNL Table with Mapping:")
    print("=" * 100)
    print(f"{'Symbol':<30} {'Type':<6} {'Bid':>10} {'Ask':>10} {'Spread':>10}")
    print("-" * 100)
    
    cursor.execute("""
        SELECT symbol, bid, ask, 
               CASE WHEN bid IS NOT NULL AND ask IS NOT NULL 
                    THEN ask - bid 
                    ELSE NULL 
               END as spread
        FROM FULLPNL 
        ORDER BY symbol
    """)
    
    for row in cursor.fetchall():
        symbol, bid, ask, spread = row
        
        # Determine type
        parsed = parse_bloomberg_symbol(symbol)
        sym_type = parsed['type'] if parsed else 'UNK'
        
        bid_str = f"{bid:.6f}" if bid is not None else "NULL"
        ask_str = f"{ask:.6f}" if ask is not None else "NULL"
        spread_str = f"{spread:.6f}" if spread is not None else "NULL"
        print(f"{symbol:<30} {sym_type:<6} {bid_str:>10} {ask_str:>10} {spread_str:>10}")
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(bid) as with_bid,
            COUNT(ask) as with_ask,
            COUNT(CASE WHEN bid IS NOT NULL AND ask IS NOT NULL THEN 1 END) as with_both
        FROM FULLPNL
    """)
    
    total, with_bid, with_ask, with_both = cursor.fetchone()
    print("\nSummary:")
    print(f"  Total symbols: {total}")
    print(f"  With bid data: {with_bid} ({with_bid/total*100:.1f}%)")
    print(f"  With ask data: {with_ask} ({with_ask/total*100:.1f}%)")
    print(f"  With both: {with_both} ({with_both/total*100:.1f}%)")


def main():
    """Main function to add bid/ask using symbol mapping."""
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    pnl_db_path = os.path.join(project_root, "data", "output", "pnl", "pnl_tracker.db")
    
    # Find latest CSV file
    csv_dirs = [
        os.path.join(project_root, "data", "output", "spot_risk", "2025-07-18"),
        os.path.join(project_root, "data", "output", "spot_risk", "processed", "2025-07-16")
    ]
    
    csv_path = None
    for csv_dir in csv_dirs:
        if os.path.exists(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) 
                        if f.startswith('bav_analysis_processed_') and f.endswith('.csv')]
            if csv_files:
                csv_path = os.path.join(csv_dir, sorted(csv_files)[-1])
                break
    
    if not csv_path:
        logger.error("No spot risk CSV files found")
        return
    
    logger.info(f"Using CSV file: {csv_path}")
    
    # Connect to database
    conn = sqlite3.connect(pnl_db_path)
    
    try:
        # Get all symbols from FULLPNL
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM FULLPNL")
        symbols = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(symbols)} symbols in FULLPNL")
        
        # Find matches and update
        matches = find_matching_spot_risk_data(csv_path, symbols)
        logger.info(f"Found {len(matches)} matches")
        
        if matches:
            update_fullpnl_with_matches(conn, matches)
        
        # Display results
        display_results(conn)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("Adding bid and ask to FULLPNL with symbol mapping")
    print("=" * 60)
    main() 