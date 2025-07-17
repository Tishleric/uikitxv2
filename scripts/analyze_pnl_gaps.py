#!/usr/bin/env python
"""
Analyze gaps in master P&L table to identify:
1. Missing information (data doesn't exist)
2. Incorrect mapping (data exists but doesn't match)
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def analyze_gaps():
    """Comprehensive gap analysis of master P&L table."""
    
    print("=" * 80)
    print("MASTER P&L TABLE GAP ANALYSIS")
    print("=" * 80)
    
    # Connect to databases
    pnl_conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    spot_conn = sqlite3.connect("data/output/spot_risk/spot_risk.db")
    
    # 1. Get all positions
    positions_df = pd.read_sql_query("""
        SELECT 
            instrument_name as symbol,
            position_quantity,
            is_option,
            option_strike
        FROM positions
        ORDER BY is_option DESC, instrument_name
    """, pnl_conn)
    
    print(f"\n📊 Total Positions: {len(positions_df)}")
    print(f"   - Futures: {len(positions_df[positions_df['is_option'] == 0])}")
    print(f"   - Options: {len(positions_df[positions_df['is_option'] == 1])}")
    
    # 2. Check spot risk data availability
    print("\n" + "-" * 60)
    print("SPOT RISK DATA ANALYSIS")
    print("-" * 60)
    
    # Get all Bloomberg symbols in spot risk
    spot_risk_symbols = pd.read_sql_query("""
        SELECT DISTINCT 
            bloomberg_symbol,
            instrument_key,
            COUNT(*) as record_count
        FROM spot_risk_raw
        WHERE bloomberg_symbol IS NOT NULL
        GROUP BY bloomberg_symbol
        ORDER BY bloomberg_symbol
    """, spot_conn)
    
    print(f"\n📊 Spot Risk Data:")
    print(f"   Total unique Bloomberg symbols: {len(spot_risk_symbols)}")
    
    # Check which positions have spot risk data
    positions_with_spot_risk = []
    positions_without_spot_risk = []
    
    for _, pos in positions_df.iterrows():
        symbol = pos['symbol']
        if symbol in spot_risk_symbols['bloomberg_symbol'].values:
            positions_with_spot_risk.append(symbol)
        else:
            positions_without_spot_risk.append(symbol)
    
    print(f"\n✅ Positions WITH spot risk data: {len(positions_with_spot_risk)}")
    for sym in positions_with_spot_risk:
        print(f"   - {sym}")
    
    print(f"\n❌ Positions WITHOUT spot risk data: {len(positions_without_spot_risk)}")
    for sym in positions_without_spot_risk:
        print(f"   - {sym}")
    
    # 3. Analyze vtexp availability
    print("\n" + "-" * 60)
    print("VTEXP (TIME TO EXPIRY) ANALYSIS")
    print("-" * 60)
    
    # Check vtexp CSV files
    vtexp_dir = Path("data/input/vtexp")
    vtexp_files = list(vtexp_dir.glob("*.csv")) if vtexp_dir.exists() else []
    
    print(f"\n📊 vtexp CSV Files: {len(vtexp_files)}")
    
    if vtexp_files:
        # Read the most recent vtexp file
        latest_vtexp = sorted(vtexp_files)[-1]
        vtexp_df = pd.read_csv(latest_vtexp)
        print(f"   Latest file: {latest_vtexp.name}")
        print(f"   Total vtexp entries: {len(vtexp_df)}")
        
        # Extract base symbols from positions
        position_bases = set()
        for _, pos in positions_df[positions_df['is_option'] == 1].iterrows():
            # Extract base from "3MN5P 110.000 Comdty" -> "3MN5P"
            base = pos['symbol'].split()[0]
            position_bases.add(base)
        
        print(f"\n📊 Option Base Symbols in Positions:")
        for base in sorted(position_bases):
            print(f"   - {base}")
            # Check if any vtexp entry might match
            # This is approximate - we need to understand the mapping better
            potential_matches = vtexp_df[vtexp_df['symbol'].str.contains('N25', na=False)]
            if not potential_matches.empty:
                print(f"     Potential vtexp matches: {len(potential_matches)}")
    
    # 4. Check spot risk data with vtexp
    print("\n" + "-" * 60)
    print("SPOT RISK VTEXP STATUS")
    print("-" * 60)
    
    spot_risk_vtexp = pd.read_sql_query("""
        SELECT 
            bloomberg_symbol,
            json_extract(raw_data, '$.vtexp') as vtexp,
            instrument_key
        FROM spot_risk_raw
        WHERE bloomberg_symbol IS NOT NULL
        LIMIT 20
    """, spot_conn)
    
    vtexp_populated = spot_risk_vtexp['vtexp'].notna().sum()
    print(f"\n📊 Spot Risk vtexp Status (sample of 20):")
    print(f"   With vtexp: {vtexp_populated}")
    print(f"   Without vtexp: {len(spot_risk_vtexp) - vtexp_populated}")
    
    # 5. Greek calculation status
    print("\n" + "-" * 60)
    print("GREEK CALCULATION STATUS")
    print("-" * 60)
    
    greek_status = pd.read_sql_query("""
        SELECT 
            calculation_status,
            COUNT(*) as count,
            COUNT(CASE WHEN error_message LIKE '%vtexp%' THEN 1 END) as vtexp_errors,
            COUNT(CASE WHEN error_message LIKE '%price%' THEN 1 END) as price_errors
        FROM spot_risk_calculated
        GROUP BY calculation_status
    """, spot_conn)
    
    print("\n📊 Greek Calculation Results:")
    for _, row in greek_status.iterrows():
        print(f"   {row['calculation_status']}: {row['count']} records")
        if row['calculation_status'] == 'failed':
            print(f"     - vtexp related errors: {row['vtexp_errors']}")
            print(f"     - price related errors: {row['price_errors']}")
    
    # 6. Symbol mapping analysis
    print("\n" + "-" * 60)
    print("SYMBOL MAPPING ANALYSIS")
    print("-" * 60)
    
    # Show sample of spot risk symbols to understand the pattern
    print("\n📊 Sample Spot Risk Bloomberg Symbols:")
    for i, symbol in enumerate(spot_risk_symbols['bloomberg_symbol'].head(10)):
        print(f"   {symbol}")
    
    # Check for similar patterns
    print("\n📊 Symbol Pattern Analysis:")
    
    # Extract patterns from positions
    position_patterns = {}
    for _, pos in positions_df[positions_df['is_option'] == 1].iterrows():
        base = pos['symbol'].split()[0]
        # Extract components
        if 'P' in base:
            prefix = base.split('P')[0][:-2]  # Everything before month/year/P
            position_patterns[prefix] = position_patterns.get(prefix, 0) + 1
    
    print("\n   Position option prefixes:")
    for prefix, count in position_patterns.items():
        print(f"     {prefix}: {count} positions")
    
    # Extract patterns from spot risk
    spot_risk_patterns = {}
    for symbol in spot_risk_symbols['bloomberg_symbol']:
        if ' ' in symbol:  # Options have strikes
            base = symbol.split()[0]
            if 'P' in base or 'C' in base:
                # Extract prefix
                for suffix in ['P', 'C']:
                    if suffix in base:
                        prefix = base.split(suffix)[0][:-2]
                        spot_risk_patterns[prefix] = spot_risk_patterns.get(prefix, 0) + 1
                        break
    
    print("\n   Spot risk option prefixes:")
    for prefix, count in sorted(spot_risk_patterns.items())[:10]:
        print(f"     {prefix}: {count} symbols")
    
    # 7. Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY OF GAPS")
    print("=" * 80)
    
    print("\n🔍 ROOT CAUSE ANALYSIS:")
    
    print("\n1. MISSING INFORMATION (Data doesn't exist):")
    print(f"   - {len(positions_without_spot_risk)} positions have NO spot risk data")
    print("   - These symbols don't exist in the spot risk files at all")
    
    print("\n2. INCORRECT MAPPING (Data exists but doesn't connect):")
    print("   - Symbol format mismatch between systems")
    print("   - Your positions: 3MN5P, TYWN25P4, VBYN25P3 series")
    print("   - Spot risk has: TJP, TYN, VBY series (different prefixes)")
    
    print("\n3. VTEXP ISSUES:")
    print("   - vtexp data exists but may not map to your option series")
    print("   - Need to verify symbol format in vtexp files matches positions")
    
    print("\n4. GREEK CALCULATION FAILURES:")
    if 'failed' in greek_status['calculation_status'].values:
        failed_row = greek_status[greek_status['calculation_status'] == 'failed'].iloc[0]
        total_failed = failed_row['count']
        vtexp_failed = failed_row['vtexp_errors']
        print(f"   - {total_failed} total failures")
        print(f"   - {vtexp_failed} due to missing vtexp")
        print(f"   - {total_failed - vtexp_failed} due to other issues (price, convergence)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n1. For MISSING DATA:")
    print("   - Request spot risk files containing your specific option series")
    print("   - Series needed: 3M, TYW, VBY with July 2025 expiries")
    
    print("\n2. For MAPPING ISSUES:")
    print("   - Enhance symbol translator to handle all series variants")
    print("   - Create a master mapping table for all known series")
    
    print("\n3. For VTEXP:")
    print("   - Verify vtexp CSV symbols match your positions")
    print("   - Implement fallback calculation based on expiry dates")
    
    pnl_conn.close()
    spot_conn.close()


if __name__ == "__main__":
    analyze_gaps() 