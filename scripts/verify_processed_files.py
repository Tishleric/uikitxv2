#!/usr/bin/env python3
"""
Verify which files have been marked as processed in the PnL database
"""

import sqlite3
import sys
import argparse
from pathlib import Path

def check_processed_files(db_path='trades.db'):
    """Check which files are marked as processed"""
    
    print(f"\nChecking processed files in {db_path}...")
    print("=" * 60)
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"Database '{db_path}' does not exist!")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if processed_files table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='processed_files'
    """)
    
    if not cursor.fetchone():
        print("processed_files table does not exist!")
        conn.close()
        return
    
    # Get all processed files
    cursor.execute("""
        SELECT file_path, processed_at, trade_count, last_modified
        FROM processed_files
        ORDER BY processed_at DESC
    """)
    
    processed_files = cursor.fetchall()
    
    if not processed_files:
        print("No files have been marked as processed yet.")
    else:
        print(f"\nFound {len(processed_files)} processed files:")
        print("-" * 60)
        for file_path, processed_at, trade_count, last_modified in processed_files:
            filename = Path(file_path).name
            status = "pre-marked" if trade_count == -1 else f"{trade_count} trades"
            print(f"{filename:<40} | {status:<15} | {processed_at}")
    
    # Check trade ledger directory
    trade_ledger_dir = Path("data/input/trade_ledger")
    if trade_ledger_dir.exists():
        print(f"\nTrade ledger files in {trade_ledger_dir}:")
        print("-" * 60)
        
        for csv_file in sorted(trade_ledger_dir.glob("trades_*.csv")):
            # Check if this file is processed
            mtime = csv_file.stat().st_mtime
            cursor.execute("""
                SELECT 1 FROM processed_files 
                WHERE file_path = ? AND last_modified = ?
            """, (str(csv_file), mtime))
            
            is_processed = cursor.fetchone() is not None
            status = "✓ Already processed" if is_processed else "✗ Will be processed"
            print(f"  {csv_file.name}: {status}")
    
    # Check spot risk directory
    spot_risk_dir = Path("data/input/actant_spot_risk")
    if spot_risk_dir.exists():
        print(f"\nSpot risk files in {spot_risk_dir}:")
        print("-" * 60)
        
        for subdir in spot_risk_dir.iterdir():
            if subdir.is_dir():
                for csv_file in sorted(subdir.glob("bav_analysis_*.csv")):
                    # Check if this file is processed
                    mtime = csv_file.stat().st_mtime
                    cursor.execute("""
                        SELECT 1 FROM processed_files 
                        WHERE file_path = ? AND last_modified = ?
                    """, (str(csv_file), mtime))
                    
                    is_processed = cursor.fetchone() is not None
                    status = "✓ Already processed" if is_processed else "✗ Will be processed"
                    print(f"  {csv_file.name}: {status}")
    
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify processed files in PnL database')
    parser.add_argument('--db', default='trades.db', help='Path to database (default: trades.db)')
    args = parser.parse_args()
    
    check_processed_files(args.db) 