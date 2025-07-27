#!/usr/bin/env python3
"""
Mark existing files as processed to prevent reprocessing historical data
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


def mark_existing_files(db_path='trades.db'):
    """Mark all existing files as processed with trade_count = -1"""
    
    print(f"\nMarking existing files as processed in {db_path}...")
    print("=" * 60)
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"Database '{db_path}' does not exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure processed_files table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            file_path TEXT PRIMARY KEY,
            processed_at TEXT,
            trade_count INTEGER,
            last_modified REAL
        )
    """)
    
    files_marked = 0
    
    # Mark trade ledger files
    trade_ledger_dir = Path('data/input/trade_ledger')
    if trade_ledger_dir.exists():
        print(f"\nChecking trade ledger files in {trade_ledger_dir}...")
        for csv_file in sorted(trade_ledger_dir.glob('trades_*.csv')):
            # Check if already marked
            cursor.execute("""
                SELECT 1 FROM processed_files WHERE file_path = ?
            """, (str(csv_file),))
            
            if not cursor.fetchone():
                # Mark as processed with -1 to indicate pre-existing
                cursor.execute("""
                    INSERT INTO processed_files (file_path, processed_at, trade_count, last_modified)
                    VALUES (?, ?, ?, ?)
                """, (
                    str(csv_file),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    -1,  # Special marker for pre-existing files
                    csv_file.stat().st_mtime
                ))
                files_marked += 1
                print(f"  Marked: {csv_file.name}")
            else:
                print(f"  Already marked: {csv_file.name}")
    
    # Mark spot risk files
    spot_risk_dir = Path('data/input/actant_spot_risk')
    if spot_risk_dir.exists():
        print(f"\nChecking spot risk files in {spot_risk_dir}...")
        for subdir in spot_risk_dir.iterdir():
            if subdir.is_dir():
                for csv_file in sorted(subdir.glob('bav_analysis_*.csv')):
                    # Check if already marked
                    cursor.execute("""
                        SELECT 1 FROM processed_files WHERE file_path = ?
                    """, (str(csv_file),))
                    
                    if not cursor.fetchone():
                        # Mark as processed
                        cursor.execute("""
                            INSERT INTO processed_files (file_path, processed_at, trade_count, last_modified)
                            VALUES (?, ?, ?, ?)
                        """, (
                            str(csv_file),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            -1,  # Special marker for pre-existing files
                            csv_file.stat().st_mtime
                        ))
                        files_marked += 1
                        print(f"  Marked: {csv_file.name}")
                    else:
                        print(f"  Already marked: {csv_file.name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Total files marked as processed: {files_marked}")
    print("These files will be skipped by the watchers.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mark existing files as processed in PnL database')
    parser.add_argument('--db', default='trades.db', help='Path to database (default: trades.db)')
    args = parser.parse_args()
    
    mark_existing_files(args.db) 