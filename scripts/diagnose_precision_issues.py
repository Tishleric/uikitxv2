#!/usr/bin/env python3
"""Diagnose floating point precision issues in P&L calculations."""

import sqlite3
from decimal import Decimal, getcontext
from pathlib import Path
import json

# Set decimal precision for financial calculations
getcontext().prec = 10


def analyze_precision_issues(db_path: str):
    """Analyze floating point precision issues in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n=== Analyzing {db_path} ===\n")
    
    # Check positions table
    print("Positions Table Analysis:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT symbol, quantity, avg_cost, market_price, 
               realized_pnl, unrealized_pnl, total_pnl
        FROM positions
        ORDER BY symbol
    """)
    
    issues_found = []
    
    for row in cursor.fetchall():
        symbol, qty, avg_cost, mkt_price, real_pnl, unreal_pnl, total_pnl = row
        
        # Check for precision issues
        for field_name, value in [
            ("avg_cost", avg_cost),
            ("market_price", mkt_price),
            ("realized_pnl", real_pnl),
            ("unrealized_pnl", unreal_pnl),
            ("total_pnl", total_pnl)
        ]:
            if value is not None:
                # Convert to string to check decimal places
                str_val = str(value)
                if '.' in str_val:
                    decimal_places = len(str_val.split('.')[1])
                    # Check if more than expected decimal places
                    if decimal_places > 5:  # Futures prices typically 5 decimals
                        issues_found.append({
                            "symbol": symbol,
                            "field": field_name,
                            "value": value,
                            "string_repr": str_val,
                            "decimal_places": decimal_places
                        })
                
                # Check if value differs from rounded version
                rounded_val = round(value, 5)
                if abs(value - rounded_val) > 1e-10:
                    issues_found.append({
                        "symbol": symbol,
                        "field": field_name,
                        "value": value,
                        "expected": rounded_val,
                        "difference": value - rounded_val
                    })
        
        print(f"{symbol:15} qty={qty:6} avg={avg_cost:12} mkt={mkt_price:12} "
              f"real={real_pnl:12} unreal={unreal_pnl:12} total={total_pnl:12}")
    
    # Check snapshots table  
    print("\n\nPosition Snapshots Analysis:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT snapshot_time, symbol, quantity, avg_cost, market_price,
               realized_pnl, unrealized_pnl, total_pnl
        FROM position_snapshots
        ORDER BY snapshot_time, symbol
        LIMIT 20
    """)
    
    for row in cursor.fetchall():
        time, symbol, qty, avg_cost, mkt_price, real_pnl, unreal_pnl, total_pnl = row
        print(f"{time} {symbol:15} qty={qty:6} real={real_pnl:12} "
              f"unreal={unreal_pnl:12} total={total_pnl:12}")
    
    # Report issues
    if issues_found:
        print("\n\n⚠️  PRECISION ISSUES FOUND:")
        print("-" * 80)
        for issue in issues_found[:10]:  # Show first 10
            print(json.dumps(issue, indent=2))
        if len(issues_found) > 10:
            print(f"\n... and {len(issues_found) - 10} more issues")
    else:
        print("\n✓ No precision issues found")
    
    # Check calculation methods
    print("\n\nCalculation Chain Analysis:")
    print("-" * 80)
    
    # Get a sample position with P&L
    cursor.execute("""
        SELECT symbol, quantity, avg_cost, market_price
        FROM positions
        WHERE unrealized_pnl != 0
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if row:
        symbol, qty, avg_cost, mkt_price = row
        print(f"\nExample: {symbol}")
        print(f"Quantity: {qty}")
        print(f"Avg Cost: {avg_cost} (repr: {repr(avg_cost)})")
        print(f"Market Price: {mkt_price} (repr: {repr(mkt_price)})")
        
        # Reproduce calculation with different methods
        print("\nCalculation Methods:")
        
        # Float calculation
        float_pnl = qty * (mkt_price - avg_cost)
        print(f"Float: {qty} * ({mkt_price} - {avg_cost}) = {float_pnl}")
        print(f"       repr: {repr(float_pnl)}")
        
        # Decimal calculation
        dec_qty = Decimal(str(qty))
        dec_mkt = Decimal(str(mkt_price))
        dec_avg = Decimal(str(avg_cost))
        dec_pnl = dec_qty * (dec_mkt - dec_avg)
        print(f"Decimal: {dec_qty} * ({dec_mkt} - {dec_avg}) = {dec_pnl}")
        
        # Compare
        diff = float(dec_pnl) - float_pnl
        print(f"Difference: {diff}")
    
    conn.close()


def check_calculation_source():
    """Check the source code for floating point operations."""
    print("\n\n=== Source Code Analysis ===\n")
    
    files_to_check = [
        "lib/trading/pnl_calculator/calculator.py",
        "lib/trading/pnl_calculator/position_manager.py",
        "lib/trading/pnl_calculator/service.py"
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"\nChecking {file_path}:")
            print("-" * 40)
            
            content = path.read_text()
            lines = content.split('\n')
            
            # Look for potential precision issues
            for i, line in enumerate(lines, 1):
                # Check for direct float arithmetic
                if any(op in line for op in ['*', '/', '+', '-']) and 'Decimal' not in line:
                    if any(term in line.lower() for term in ['price', 'cost', 'pnl', 'value']):
                        print(f"Line {i}: {line.strip()}")


if __name__ == "__main__":
    # Check test database
    test_db = "data/output/pnl/pnl_tracker_test.db"
    if Path(test_db).exists():
        analyze_precision_issues(test_db)
    
    # Check production database
    prod_db = "data/output/pnl/pnl_tracker.db"
    if Path(prod_db).exists():
        analyze_precision_issues(prod_db)
    
    # Check source code
    check_calculation_source() 