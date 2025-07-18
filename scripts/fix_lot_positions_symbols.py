#!/usr/bin/env python
"""Fix lot_positions symbols to use consistent Bloomberg format."""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def fix_lot_symbols():
    """Update lot_positions to use consistent Bloomberg format."""
    
    print("=" * 80)
    print("FIX LOT POSITIONS SYMBOLS TO BLOOMBERG FORMAT")
    print("=" * 80)
    
    db_path = "data/output/pnl/pnl_tracker.db"
    
    # Backup database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    
    # Show current state
    print("\n1. Current lot_positions symbols:")
    print("-" * 60)
    query = """
    SELECT DISTINCT symbol, COUNT(*) as lot_count
    FROM lot_positions
    GROUP BY symbol
    ORDER BY symbol
    """
    
    current_df = pd.read_sql_query(query, conn)
    print(current_df)
    
    # Find symbols that need fixing (VY3N5, WY4N5, etc.)
    print("\n2. Symbols needing Bloomberg format:")
    print("-" * 60)
    
    symbols_to_fix = []
    for symbol in current_df['symbol']:
        if not symbol.endswith(' Comdty'):
            symbols_to_fix.append(symbol)
            print(f"  - {symbol}")
    
    if not symbols_to_fix:
        print("  None - all symbols already in Bloomberg format!")
        return
    
    # Map these symbols to their Bloomberg equivalents
    print("\n3. Mapping to Bloomberg format:")
    print("-" * 60)
    
    for symbol in symbols_to_fix:
        # Get the associated position_id to find the correct Bloomberg symbol
        cursor = conn.execute("""
            SELECT DISTINCT l.position_id, p.instrument_name
            FROM lot_positions l
            LEFT JOIN positions p ON l.position_id = p.id
            WHERE l.symbol = ?
            AND l.position_id IS NOT NULL
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        if result and result[1]:
            bloomberg_symbol = result[1]
            print(f"  {symbol} -> {bloomberg_symbol}")
            
            # Update all lot_positions with this symbol
            conn.execute("""
                UPDATE lot_positions
                SET symbol = ?
                WHERE symbol = ?
            """, (bloomberg_symbol, symbol))
        else:
            # For symbols without position_id, we need to construct Bloomberg format
            # This handles cases where position_id might be NULL
            if any(prefix in symbol for prefix in ['VY', 'GY', 'WY', 'HY']):
                # Weekly options - need to find from positions table
                print(f"  {symbol} -> Need to find Bloomberg equivalent...")
                
                # Try to match based on the base symbol
                base_mapping = {
                    'VY': 'VBYN25P',
                    'GY': 'TJPN25P',
                    'WY': 'TYWN25P',
                    'HY': 'TJWN25P'
                }
                
                for prefix, bloomberg_base in base_mapping.items():
                    if symbol.startswith(prefix):
                        # Find any matching position
                        cursor = conn.execute("""
                            SELECT DISTINCT instrument_name
                            FROM positions
                            WHERE instrument_name LIKE ?
                            LIMIT 1
                        """, (bloomberg_base + '%',))
                        
                        result = cursor.fetchone()
                        if result:
                            # Use first match as template
                            bloomberg_symbol = symbol + " Comdty"  # Simple fallback
                            print(f"    Using fallback: {symbol} -> {bloomberg_symbol}")
                            
                            conn.execute("""
                                UPDATE lot_positions
                                SET symbol = ?
                                WHERE symbol = ?
                            """, (bloomberg_symbol, symbol))
            else:
                # For futures, just add " Comdty"
                bloomberg_symbol = f"{symbol} Comdty"
                print(f"  {symbol} -> {bloomberg_symbol}")
                
                conn.execute("""
                    UPDATE lot_positions
                    SET symbol = ?
                    WHERE symbol = ?
                """, (bloomberg_symbol, symbol))
    
    # Commit changes
    conn.commit()
    
    # Show after state
    print("\n4. After fix - lot_positions symbols:")
    print("-" * 60)
    
    after_df = pd.read_sql_query(query, conn)
    print(after_df)
    
    conn.close()
    
    print("\n✓ Fix complete!")
    print(f"✓ Backup saved at: {backup_path}")

if __name__ == "__main__":
    fix_lot_symbols() 