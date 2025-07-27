#!/usr/bin/env python3
"""Monitor spot risk pipeline processing health."""

import sys
sys.path.append('.')

from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def monitor_pipeline():
    """Monitor spot risk pipeline health metrics."""
    
    print("=== SPOT RISK PIPELINE MONITORING ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check database
    db_path = Path("data/output/spot_risk/spot_risk.db")
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 1. Check recent sessions
    print("1. Recent Processing Sessions:")
    sessions_query = """
    SELECT session_id, source_file, data_timestamp, status, 
           row_count, error_count, start_time
    FROM spot_risk_sessions
    ORDER BY start_time DESC
    LIMIT 5
    """
    sessions_df = pd.read_sql_query(sessions_query, conn)
    
    if sessions_df.empty:
        print("  No sessions found")
    else:
        for _, row in sessions_df.iterrows():
            status_icon = "✅" if row['status'] == 'completed' else "❌"
            print(f"  {status_icon} {row['source_file'].split('/')[-1]} - "
                  f"{row['row_count']} rows, {row['error_count']} errors")
    
    # 2. Check Bloomberg translation rate
    print("\n2. Bloomberg Symbol Translation:")
    translation_query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN bloomberg_symbol IS NOT NULL THEN 1 ELSE 0 END) as translated
    FROM spot_risk_raw
    WHERE session_id = (SELECT MAX(session_id) FROM spot_risk_sessions)
    """
    trans_result = pd.read_sql_query(translation_query, conn)
    
    if not trans_result.empty:
        total = trans_result.iloc[0]['total']
        translated = trans_result.iloc[0]['translated']
        rate = (translated / total * 100) if total > 0 else 0
        print(f"  Latest session: {translated}/{total} ({rate:.1f}%)")
    
    # 3. Check vtexp matching (for options only)
    print("\n3. vtexp Matching (Options):")
    vtexp_query = """
    SELECT 
        COUNT(*) as total_options,
        SUM(CASE WHEN vtexp IS NOT NULL THEN 1 ELSE 0 END) as with_vtexp
    FROM spot_risk_raw
    WHERE instrument_type IN ('C', 'P', 'call', 'put')
    AND session_id = (SELECT MAX(session_id) FROM spot_risk_sessions)
    """
    vtexp_result = pd.read_sql_query(vtexp_query, conn)
    
    if not vtexp_result.empty:
        total_opt = vtexp_result.iloc[0]['total_options']
        with_vtexp = vtexp_result.iloc[0]['with_vtexp']
        rate = (with_vtexp / total_opt * 100) if total_opt > 0 else 0
        print(f"  Latest session: {with_vtexp}/{total_opt} ({rate:.1f}%)")
    
    # 4. Check Greek calculation success
    print("\n4. Greek Calculations:")
    greek_query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN calculation_status = 'success' THEN 1 ELSE 0 END) as successful
    FROM spot_risk_calculated
    WHERE session_id = (SELECT MAX(session_id) FROM spot_risk_sessions)
    """
    greek_result = pd.read_sql_query(greek_query, conn)
    
    if not greek_result.empty:
        total_calc = greek_result.iloc[0]['total']
        successful = greek_result.iloc[0]['successful']
        rate = (successful / total_calc * 100) if total_calc > 0 else 0
        print(f"  Latest session: {successful}/{total_calc} ({rate:.1f}%)")
    
    # 5. Check for unprocessed files
    print("\n5. Unprocessed Files:")
    input_dir = Path("data/input/actant_spot_risk")
    output_dir = Path("data/output/spot_risk/processed")
    
    # Get all input files
    input_files = list(input_dir.rglob("bav_analysis_*.csv"))
    
    # Check which ones have been processed
    unprocessed = []
    for input_file in input_files:
        # Check if corresponding processed file exists
        timestamp_parts = input_file.stem.split('_')
        if len(timestamp_parts) >= 4:
            timestamp = f"{timestamp_parts[2]}_{timestamp_parts[3]}"
            processed_name = f"bav_analysis_processed_{timestamp}.csv"
            
            # Check in all subdirectories
            if not any(output_dir.rglob(processed_name)):
                unprocessed.append(input_file)
    
    if unprocessed:
        print(f"  Found {len(unprocessed)} unprocessed files:")
        for f in unprocessed[:5]:  # Show first 5
            print(f"    - {f.relative_to(input_dir)}")
    else:
        print("  ✅ All files processed")
    
    # 6. Overall health summary
    print("\n" + "="*50)
    print("OVERALL PIPELINE HEALTH:")
    
    # Define health thresholds
    health_issues = []
    
    if 'rate' in locals() and rate < 90:
        health_issues.append(f"Low translation rate: {rate:.1f}%")
    
    if 'vtexp_rate' in locals() and vtexp_rate < 90:
        health_issues.append(f"Low vtexp match rate: {vtexp_rate:.1f}%")
    
    if 'greek_rate' in locals() and greek_rate < 80:
        health_issues.append(f"Low Greek success rate: {greek_rate:.1f}%")
    
    if len(unprocessed) > 0:
        health_issues.append(f"{len(unprocessed)} files unprocessed")
    
    if health_issues:
        print("⚠️  ISSUES DETECTED:")
        for issue in health_issues:
            print(f"  - {issue}")
    else:
        print("✅ PIPELINE HEALTHY")
    
    conn.close()

if __name__ == "__main__":
    monitor_pipeline() 