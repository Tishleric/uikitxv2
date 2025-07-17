#!/usr/bin/env python3
"""Check the schema of spot_risk_raw table."""

import sqlite3
import pandas as pd

def check_schema():
    """Check and display the schema of spot_risk_raw table."""
    conn = sqlite3.connect('data/output/spot_risk/spot_risk.db')
    
    # Get table info
    print("=== SPOT_RISK_RAW TABLE SCHEMA ===")
    table_info = pd.read_sql("PRAGMA table_info(spot_risk_raw)", conn)
    print(table_info)
    
    # Get sample data
    print("\n=== SAMPLE DATA ===")
    sample = pd.read_sql("SELECT * FROM spot_risk_raw LIMIT 3", conn)
    print(sample)
    
    # Check for raw_data column
    print("\n=== RAW_DATA COLUMN CHECK ===")
    if 'raw_data' in table_info['name'].values:
        print("raw_data column exists - checking content type...")
        raw_sample = pd.read_sql("SELECT id, instrument_key, raw_data FROM spot_risk_raw LIMIT 1", conn)
        print(raw_sample)
    
    conn.close()

if __name__ == "__main__":
    check_schema() 