#!/usr/bin/env python3
"""
Diagnose why options are not getting prior_close data from market_prices.db
"""
import sqlite3
from pathlib import Path

def diagnose_options_prior_close():
    """Investigate options_prices table for prior_close data."""
    
    # Database paths
    project_root = Path(__file__).parent.parent.parent
    market_prices_db_path = project_root / "data/output/market_prices/market_prices.db"
    
    if not market_prices_db_path.exists():
        print(f"Error: Market prices database not found at {market_prices_db_path}")
        return
    
    conn = sqlite3.connect(market_prices_db_path)
    cursor = conn.cursor()
    
    print("="*80)
    print("DIAGNOSING OPTIONS PRIOR_CLOSE DATA")
    print("="*80)
    
    # First, let's see how many options have prior_close data
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(prior_close) as with_prior_close,
               COUNT(CASE WHEN prior_close IS NOT NULL AND prior_close != 0 THEN 1 END) as non_zero_prior_close
        FROM options_prices
    """)
    total, with_pc, non_zero_pc = cursor.fetchone()
    print(f"\nOptions Statistics:")
    print(f"Total option records: {total}")
    print(f"Records with prior_close: {with_pc} ({with_pc/total*100:.1f}%)")
    print(f"Records with non-zero prior_close: {non_zero_pc} ({non_zero_pc/total*100:.1f}%)")
    
    # Now let's look at our specific symbols
    our_symbols = [
        '3MN5P 110.000 Comdty',
        '3MN5P 110.250 Comdty',
        'TYWN25P4 109.750 Comdty',
        'TYWN25P4 110.500 Comdty',
        'VBYN25P3 109.500 Comdty',
        'VBYN25P3 110.000 Comdty',
        'VBYN25P3 110.250 Comdty'
    ]
    
    print(f"\n{'='*80}")
    print("CHECKING OUR SPECIFIC OPTION SYMBOLS:")
    print(f"{'='*80}")
    
    for symbol in our_symbols:
        cursor.execute("""
            SELECT symbol, current_price, prior_close, trade_date, last_updated
            FROM options_prices
            WHERE symbol = ?
            ORDER BY last_updated DESC
        """, (symbol,))
        
        results = cursor.fetchall()
        print(f"\n{symbol}:")
        if results:
            for row in results:
                s, cp, pc, td, lu = row
                print(f"  Trade Date: {td}, Current: {cp}, Prior Close: {pc}, Updated: {lu}")
        else:
            print("  NOT FOUND IN TABLE")
    
    # Let's check if there's a pattern in symbols that DO have prior_close
    print(f"\n{'='*80}")
    print("SAMPLE OPTIONS WITH PRIOR_CLOSE DATA:")
    print(f"{'='*80}")
    
    cursor.execute("""
        SELECT symbol, current_price, prior_close, trade_date
        FROM options_prices
        WHERE prior_close IS NOT NULL AND prior_close != 0
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"{'Symbol':<40} {'Current':>10} {'Prior Close':>12} {'Trade Date'}")
        print("-"*75)
        for symbol, cp, pc, td in results:
            print(f"{symbol:<40} {cp if cp else 'NULL':>10} {pc:>12.6f} {td}")
    else:
        print("No options found with prior_close data!")
    
    # Let's check distinct values in prior_close column
    print(f"\n{'='*80}")
    print("DISTINCT PRIOR_CLOSE VALUES:")
    print(f"{'='*80}")
    
    cursor.execute("""
        SELECT DISTINCT prior_close, COUNT(*) as count
        FROM options_prices
        GROUP BY prior_close
        ORDER BY count DESC
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    print(f"{'Prior Close':>15} {'Count':>10}")
    print("-"*25)
    for pc, count in results:
        pc_str = f"{pc:.6f}" if pc is not None else "NULL"
        print(f"{pc_str:>15} {count:>10}")
    
    # Check if our symbols exist with different formatting
    print(f"\n{'='*80}")
    print("SEARCHING FOR PARTIAL MATCHES:")
    print(f"{'='*80}")
    
    for symbol in our_symbols:
        # Extract the base part (e.g., "3MN5P 110.000")
        base_part = symbol.replace(" Comdty", "")
        
        cursor.execute("""
            SELECT DISTINCT symbol
            FROM options_prices
            WHERE symbol LIKE ?
            LIMIT 5
        """, (f"%{base_part}%",))
        
        matches = cursor.fetchall()
        if matches:
            print(f"\nMatches for '{base_part}':")
            for (match,) in matches:
                print(f"  {match}")
    
    conn.close()

if __name__ == "__main__":
    diagnose_options_prior_close() 