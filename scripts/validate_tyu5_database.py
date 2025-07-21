#!/usr/bin/env python3
"""
Validate TYU5 database contents against Excel output.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys


def validate_tyu5_database():
    """Validate database contents match Excel output structure."""
    print("TYU5 Database Validation")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    db_path = 'data/output/pnl/pnl_tracker.db'
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    # Get latest run info
    try:
        cursor = conn.execute("""
            SELECT * FROM tyu5_runs 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        columns = [desc[0] for desc in cursor.description]
        latest_run = cursor.fetchone()
        
        if latest_run:
            run_info = dict(zip(columns, latest_run))
            print("\nLATEST RUN:")
            print(f"  Run ID: {run_info['run_id']}")
            print(f"  Timestamp: {run_info['timestamp']}")
            print(f"  Status: {run_info['status']}")
            print(f"  Excel File: {run_info['excel_file_path']}")
            print(f"  Total P&L: ${run_info['total_pnl']:,.2f}" if run_info['total_pnl'] else "  Total P&L: N/A")
            
            if run_info['error_message']:
                print(f"  Error: {run_info['error_message']}")
        else:
            print("\nNo runs found in tyu5_runs table")
            return False
            
    except Exception as e:
        print(f"\nERROR reading tyu5_runs: {e}")
        return False
    
    # Validate each table
    print("\nTABLE VALIDATION:")
    print("-" * 80)
    
    expected_tables = {
        'tyu5_trades': {
            'excel_sheet': 'Trades',
            'key_columns': ['Symbol', 'Action', 'Quantity', 'Price_Decimal', 'Realized_PNL'],
            'numeric_columns': ['Quantity', 'Price_Decimal', 'Realized_PNL', 'Fees']
        },
        'tyu5_positions': {
            'excel_sheet': 'Positions',
            'key_columns': ['Symbol', 'Net_Quantity', 'Closed_Quantity', 'Realized_PNL', 'Total_PNL'],
            'numeric_columns': ['Net_Quantity', 'Closed_Quantity', 'Avg_Entry_Price', 'Realized_PNL', 'Total_PNL']
        },
        'tyu5_summary': {
            'excel_sheet': 'Summary',
            'key_columns': ['Metric', 'Value', 'Details'],
            'numeric_columns': ['Value']
        },
        'tyu5_risk_matrix': {
            'excel_sheet': 'Risk_Matrix',
            'key_columns': ['Position_ID', 'TYU5_Price', 'Scenario_PNL'],
            'numeric_columns': ['TYU5_Price', 'Price_Change', 'Scenario_PNL']
        },
        'tyu5_position_breakdown': {
            'excel_sheet': 'Position_Breakdown',
            'key_columns': ['Symbol', 'Label', 'Description'],
            'numeric_columns': ['Quantity', 'Inception_PNL']  # Mixed types
        }
    }
    
    all_valid = True
    
    for table_name, config in expected_tables.items():
        print(f"\nValidating {table_name}:")
        
        try:
            # Check if table exists
            cursor = conn.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            if not cursor.fetchone():
                print(f"  ✗ ERROR: Table {table_name} does not exist")
                all_valid = False
                continue
            
            # Get table info
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            print(f"  ✓ Table exists: {len(df)} rows, {len(df.columns)} columns")
            
            # Check key columns exist
            missing_cols = [col for col in config['key_columns'] if col not in df.columns]
            if missing_cols:
                print(f"  ✗ ERROR: Missing columns: {missing_cols}")
                all_valid = False
            else:
                print(f"  ✓ All key columns present")
            
            # Check numeric columns are numeric
            numeric_issues = []
            for col in config['numeric_columns']:
                if col in df.columns:
                    # Check if column contains any non-numeric non-null values
                    non_numeric = df[col].apply(lambda x: x is not None and not isinstance(x, (int, float)) and not pd.isna(x))
                    if non_numeric.any():
                        numeric_issues.append(col)
            
            if numeric_issues:
                print(f"  ✗ WARNING: Non-numeric values in columns: {numeric_issues}")
            else:
                print(f"  ✓ Numeric columns validated")
            
            # Special checks for specific tables
            if table_name == 'tyu5_positions':
                # Check VY3N5 closed quantity
                vy3_rows = df[df['Symbol'].str.startswith('VY3N5')]
                if not vy3_rows.empty:
                    vy3 = vy3_rows.iloc[0]
                    if vy3['Closed_Quantity'] == 100.0 and vy3['Realized_PNL'] == 2800.0:
                        print(f"  ✓ VY3N5 closed position verified")
                    else:
                        print(f"  ✗ WARNING: VY3N5 values unexpected")
                        print(f"    Expected: Closed=100.0, Realized=$2,800.00")
                        print(f"    Actual: Closed={vy3['Closed_Quantity']}, Realized=${vy3['Realized_PNL']:,.2f}")
                        
            elif table_name == 'tyu5_summary':
                # Check for Total PNL metric
                total_row = df[df['Metric'] == 'Total PNL']
                if not total_row.empty:
                    total_pnl = total_row.iloc[0]['Value']
                    print(f"  ✓ Total PNL metric found: ${total_pnl:,.2f}")
                else:
                    print(f"  ✗ WARNING: No Total PNL metric in summary")
                    
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            all_valid = False
    
    # Compare with Excel if file exists
    if run_info and run_info['excel_file_path'] and os.path.exists(run_info['excel_file_path']):
        print("\n" + "-" * 80)
        print("EXCEL COMPARISON:")
        compare_with_excel(conn, run_info['excel_file_path'], expected_tables)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"Validation {'PASSED' if all_valid else 'FAILED'}")
    
    return all_valid


def compare_with_excel(conn, excel_path, expected_tables):
    """Compare database tables with Excel sheets."""
    try:
        for table_name, config in expected_tables.items():
            sheet_name = config['excel_sheet']
            
            # Read from database
            db_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Read from Excel
            excel_df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            print(f"\n{table_name} vs {sheet_name}:")
            print(f"  Database rows: {len(db_df)}, Excel rows: {len(excel_df)}")
            
            if len(db_df) != len(excel_df):
                print(f"  ✗ WARNING: Row count mismatch")
            else:
                print(f"  ✓ Row count matches")
            
            # Check columns
            db_cols = set(db_df.columns)
            excel_cols = set(excel_df.columns)
            
            if db_cols != excel_cols:
                missing_in_db = excel_cols - db_cols
                extra_in_db = db_cols - excel_cols
                if missing_in_db:
                    print(f"  ✗ Missing in DB: {missing_in_db}")
                if extra_in_db:
                    print(f"  ✗ Extra in DB: {extra_in_db}")
            else:
                print(f"  ✓ Column names match")
                
    except Exception as e:
        print(f"\nERROR comparing with Excel: {e}")


if __name__ == "__main__":
    success = validate_tyu5_database()
    sys.exit(0 if success else 1) 