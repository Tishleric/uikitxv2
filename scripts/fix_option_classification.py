#!/usr/bin/env python
"""
Fix option classification in positions table.

Current issue: All positions have is_option=0, but symbols like "3MN5P 110.000 Comdty" 
are clearly options (P = Put, 110.000 = strike).
"""

import sys
from pathlib import Path
import sqlite3
import re
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_option_symbol(symbol: str) -> bool:
    """
    Determine if a Bloomberg symbol represents an option.
    
    Options have:
    - Strike price (numeric value with decimals)
    - Put/Call indicator in the symbol
    
    Examples:
    - "3MN5P 110.000 Comdty" -> Option (Put)
    - "VBYN25P3 109.500 Comdty" -> Option (Put) 
    - "TYU5 Comdty" -> Future (no strike)
    """
    # Remove "Comdty" suffix
    symbol_part = symbol.replace(" Comdty", "").strip()
    
    # Check if there's a strike price (space followed by number)
    if " " in symbol_part:
        parts = symbol_part.split()
        if len(parts) == 2:
            try:
                # Try to parse the second part as a float (strike price)
                float(parts[1])
                return True
            except ValueError:
                pass
    
    # Also check for embedded P or C in the symbol (before any space)
    # Pattern: Product + Month + Year + P/C + Series
    base_symbol = symbol_part.split()[0] if " " in symbol_part else symbol_part
    
    # Check if symbol contains P or C followed by a digit (like P3, C2)
    if re.search(r'[PC]\d', base_symbol):
        return True
        
    return False


def extract_option_details(symbol: str):
    """Extract strike price and option type from symbol."""
    symbol_part = symbol.replace(" Comdty", "").strip()
    
    strike = None
    option_type = None
    
    # Extract strike price if present
    if " " in symbol_part:
        parts = symbol_part.split()
        if len(parts) == 2:
            try:
                strike = float(parts[1])
            except ValueError:
                pass
    
    # Extract option type (P or C)
    base_symbol = symbol_part.split()[0] if " " in symbol_part else symbol_part
    
    # Look for P or C in the symbol
    if 'P' in base_symbol:
        option_type = 'PUT'
    elif 'C' in base_symbol:
        option_type = 'CALL'
    
    return strike, option_type


def fix_option_classification():
    """Fix is_option flag and related fields in positions table."""
    
    db_path = "data/output/pnl/pnl_tracker.db"
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all positions
    cursor.execute("SELECT id, instrument_name, is_option FROM positions")
    positions = cursor.fetchall()
    
    updates = []
    for pos_id, symbol, current_is_option in positions:
        should_be_option = is_option_symbol(symbol)
        
        if should_be_option != bool(current_is_option):
            strike, option_type = extract_option_details(symbol)
            updates.append((pos_id, symbol, should_be_option, strike, option_type))
    
    if updates:
        logger.info(f"Found {len(updates)} positions to update")
        
        for pos_id, symbol, is_option, strike, option_type in updates:
            logger.info(f"Updating {symbol}: is_option={is_option}, strike={strike}, type={option_type}")
            
            cursor.execute("""
                UPDATE positions 
                SET is_option = ?,
                    option_strike = ?
                WHERE id = ?
            """, (1 if is_option else 0, strike, pos_id))
        
        conn.commit()
        logger.info(f"Updated {len(updates)} positions")
        
        # Verify the updates
        cursor.execute("SELECT COUNT(*) FROM positions WHERE is_option = 1")
        option_count = cursor.fetchone()[0]
        logger.info(f"Total options after update: {option_count}")
    else:
        logger.info("No positions need updating")
    
    # Display current status
    print("\n" + "=" * 60)
    print("POSITION CLASSIFICATION SUMMARY")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            instrument_name,
            is_option,
            option_strike,
            position_quantity
        FROM positions
        ORDER BY is_option DESC, instrument_name
    """)
    
    print("\n{:<30} {:<10} {:<10} {:<10}".format("Symbol", "Is Option", "Strike", "Quantity"))
    print("-" * 60)
    
    for row in cursor.fetchall():
        symbol, is_opt, strike, qty = row
        print("{:<30} {:<10} {:<10} {:<10}".format(
            symbol,
            "Yes" if is_opt else "No",
            f"{strike:.3f}" if strike else "-",
            f"{qty:.0f}"
        ))
    
    conn.close()


if __name__ == "__main__":
    fix_option_classification() 