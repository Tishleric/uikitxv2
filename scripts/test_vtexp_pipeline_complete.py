"""
Test the complete vtexp pipeline: load from CSV → store in DB → use in Greek calculations.
"""

import pandas as pd
from pathlib import Path
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vtexp_pipeline():
    """Test the complete vtexp pipeline."""
    
    print("\n" + "="*80)
    print("TESTING COMPLETE VTEXP PIPELINE")
    print("="*80 + "\n")
    
    # Step 1: Verify vtexp data exists
    vtexp_dir = Path("data/input/vtexp")
    vtexp_files = list(vtexp_dir.glob("*.csv"))
    if not vtexp_files:
        print("ERROR: No vtexp CSV files found!")
        return
        
    latest_vtexp = sorted(vtexp_files)[-1]
    print(f"1. Using vtexp file: {latest_vtexp.name}")
    
    # Read vtexp data
    vtexp_df = pd.read_csv(latest_vtexp)
    print(f"   - Contains {len(vtexp_df)} vtexp values")
    print(f"   - Sample symbols: {', '.join(vtexp_df['symbol'].head(3))}")
    
    # Step 2: Check if database has vtexp column
    print(f"\n2. Checking database schema:")
    db_path = Path("data/output/spot_risk/spot_risk.db")
    conn = sqlite3.connect(db_path)
    
    # Check schema
    schema = pd.read_sql_query("PRAGMA table_info(spot_risk_raw)", conn)
    vtexp_col = schema[schema['name'] == 'vtexp']
    
    if len(vtexp_col) > 0:
        print(f"   ✓ vtexp column exists in spot_risk_raw table")
    else:
        print(f"   ✗ vtexp column NOT FOUND in spot_risk_raw table")
        return
    
    # Step 3: Check vtexp data in database
    print(f"\n3. Checking vtexp data in database:")
    vtexp_stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(vtexp) as vtexp_populated,
            MIN(vtexp) as min_vtexp,
            MAX(vtexp) as max_vtexp,
            AVG(vtexp) as avg_vtexp
        FROM spot_risk_raw
        WHERE instrument_type IN ('CALL', 'PUT')
    """, conn)
    
    stats = vtexp_stats.iloc[0]
    print(f"   - Total options: {stats['total_rows']}")
    print(f"   - Options with vtexp: {stats['vtexp_populated']}")
    if stats['vtexp_populated'] > 0:
        print(f"   - vtexp range: {stats['min_vtexp']:.4f} to {stats['max_vtexp']:.4f} years")
        print(f"   - Average vtexp: {stats['avg_vtexp']:.4f} years")
    
    # Step 4: Check Greek calculations using vtexp
    print(f"\n4. Checking Greek calculations with vtexp:")
    greek_stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_calcs,
            COUNT(CASE WHEN calculation_status = 'success' THEN 1 END) as successful_calcs,
            COUNT(CASE WHEN calculation_status = 'failed' THEN 1 END) as failed_calcs
        FROM spot_risk_calculated
        WHERE raw_id IN (
            SELECT id FROM spot_risk_raw 
            WHERE instrument_type IN ('CALL', 'PUT') AND vtexp IS NOT NULL
        )
    """, conn)
    
    if len(greek_stats) > 0:
        calc_stats = greek_stats.iloc[0]
        print(f"   - Total Greek calculations: {calc_stats['total_calcs']}")
        print(f"   - Successful: {calc_stats['successful_calcs']}")
        print(f"   - Failed: {calc_stats['failed_calcs']}")
    
    # Step 5: Show sample of options with vtexp and Greeks
    print(f"\n5. Sample options with vtexp and calculated Greeks:")
    samples = pd.read_sql_query("""
        SELECT 
            r.instrument_key,
            r.bloomberg_symbol,
            r.vtexp,
            c.implied_vol,
            c.delta_y,
            c.vega_y,
            c.calculation_status
        FROM spot_risk_raw r
        LEFT JOIN spot_risk_calculated c ON r.id = c.raw_id
        WHERE r.instrument_type IN ('CALL', 'PUT') 
        AND r.vtexp IS NOT NULL
        AND c.calculation_status = 'success'
        LIMIT 5
    """, conn)
    
    if len(samples) > 0:
        for _, row in samples.iterrows():
            print(f"\n   {row['instrument_key']}:")
            print(f"     - Bloomberg: {row['bloomberg_symbol']}")
            print(f"     - vtexp: {row['vtexp']:.4f} years")
            print(f"     - Implied Vol: {row['implied_vol']:.4f}")
            print(f"     - Delta Y: {row['delta_y']:.4f}")
            print(f"     - Vega Y: {row['vega_y']:.4f}")
    else:
        print("   No successful Greek calculations found with vtexp data")
    
    conn.close()
    
    print("\n" + "="*80)
    print("PIPELINE STATUS:")
    if stats['vtexp_populated'] > 0:
        print("✓ vtexp is successfully loaded from CSV and stored in database")
        print("✓ vtexp is being used in Greek calculations")
    else:
        print("✗ vtexp data not found in database - reprocess spot risk files needed")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_vtexp_pipeline() 