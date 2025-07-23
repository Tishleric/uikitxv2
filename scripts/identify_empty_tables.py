#!/usr/bin/env python3
"""
Identify empty tables in pnl_tracker.db and provide detailed information.

This script helps identify which tables are empty and provides context
to make informed decisions about potential cleanup. It does NOT delete
anything - only provides information.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

def get_table_info(conn: sqlite3.Connection, table_name: str) -> Dict:
    """Get detailed information about a table."""
    cursor = conn.cursor()
    
    # Get row count
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
    except sqlite3.Error:
        row_count = -1  # Error accessing table
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Get foreign key info
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    foreign_keys = cursor.fetchall()
    
    # Check if table has indexes
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    
    # Get CREATE statement
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    create_sql = cursor.fetchone()
    create_sql = create_sql[0] if create_sql else "N/A"
    
    return {
        'name': table_name,
        'row_count': row_count,
        'columns': column_names,
        'column_count': len(column_names),
        'foreign_keys': foreign_keys,
        'has_foreign_keys': len(foreign_keys) > 0,
        'indexes': indexes,
        'has_indexes': len(indexes) > 0,
        'create_sql': create_sql
    }

def categorize_tables(tables_info: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize tables by their characteristics."""
    categories = {
        'empty_no_dependencies': [],
        'empty_with_foreign_keys': [],
        'empty_with_indexes': [],
        'populated': [],
        'error_tables': []
    }
    
    for table in tables_info:
        if table['row_count'] == -1:
            categories['error_tables'].append(table)
        elif table['row_count'] == 0:
            if table['has_foreign_keys']:
                categories['empty_with_foreign_keys'].append(table)
            elif table['has_indexes']:
                categories['empty_with_indexes'].append(table)
            else:
                categories['empty_no_dependencies'].append(table)
        else:
            categories['populated'].append(table)
    
    return categories

def identify_table_purpose(table_name: str) -> str:
    """Try to identify the purpose of a table based on its name."""
    name_lower = table_name.lower()
    
    # Known table patterns
    patterns = {
        'trades': 'Trade data storage',
        'positions': 'Position tracking',
        'pnl': 'P&L calculations',
        'eod': 'End-of-day snapshots',
        'summary': 'Summary/aggregated data',
        'risk': 'Risk metrics',
        'breakdown': 'Detailed breakdown data',
        'history': 'Historical records',
        'snapshot': 'Point-in-time snapshots',
        'component': 'P&L component tracking',
        'matrix': 'Matrix/grid data',
        'temp': 'Temporary data (possibly safe to remove)',
        'backup': 'Backup data (review before removing)',
        'old': 'Old version (review before removing)',
        'test': 'Test data (possibly safe to remove)'
    }
    
    for pattern, purpose in patterns.items():
        if pattern in name_lower:
            return purpose
    
    return "Unknown purpose"

def main():
    """Main function to analyze empty tables."""
    db_path = 'data/output/pnl/pnl_tracker.db'
    
    print("=" * 80)
    print("EMPTY TABLE ANALYSIS FOR pnl_tracker.db")
    print("=" * 80)
    print(f"\nAnalyzing database: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nTotal tables found: {len(all_tables)}")
    
    # Get info for each table
    tables_info = []
    for table in all_tables:
        info = get_table_info(conn, table)
        info['purpose'] = identify_table_purpose(table)
        tables_info.append(info)
    
    # Categorize tables
    categories = categorize_tables(tables_info)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY BY CATEGORY")
    print("=" * 80)
    
    for category, tables in categories.items():
        print(f"\n{category.upper().replace('_', ' ')}: {len(tables)} tables")
    
    # Detailed empty table analysis
    print("\n" + "=" * 80)
    print("EMPTY TABLES - SAFE TO DELETE (No dependencies)")
    print("=" * 80)
    print("\nThese tables have no rows, no foreign keys, and minimal indexes:")
    
    for table in sorted(categories['empty_no_dependencies'], key=lambda x: x['name']):
        print(f"\n• {table['name']}")
        print(f"  Purpose: {table['purpose']}")
        print(f"  Columns: {', '.join(table['columns'][:5])}")
        if len(table['columns']) > 5:
            print(f"           ... and {len(table['columns']) - 5} more columns")
    
    # Empty tables with dependencies
    print("\n" + "=" * 80)
    print("EMPTY TABLES - REVIEW BEFORE DELETING (Have dependencies)")
    print("=" * 80)
    
    if categories['empty_with_foreign_keys']:
        print("\nTables with foreign keys (may be referenced by other tables):")
        for table in sorted(categories['empty_with_foreign_keys'], key=lambda x: x['name']):
            print(f"\n• {table['name']}")
            print(f"  Purpose: {table['purpose']}")
            print(f"  Foreign keys: {len(table['foreign_keys'])}")
    
    if categories['empty_with_indexes']:
        print("\nTables with indexes (may be actively used):")
        for table in sorted(categories['empty_with_indexes'], key=lambda x: x['name']):
            print(f"\n• {table['name']}")
            print(f"  Purpose: {table['purpose']}")
            print(f"  Indexes: {len(table['indexes'])}")
    
    # Populated tables summary
    print("\n" + "=" * 80)
    print("POPULATED TABLES (Do NOT delete)")
    print("=" * 80)
    print("\nThese tables contain data:")
    
    populated_sorted = sorted(categories['populated'], key=lambda x: x['row_count'], reverse=True)
    for table in populated_sorted:
        print(f"• {table['name']}: {table['row_count']:,} rows")
    
    # Generate DELETE statements (but don't execute)
    print("\n" + "=" * 80)
    print("SUGGESTED CLEANUP COMMANDS (Review carefully before running!)")
    print("=" * 80)
    print("\n⚠️  WARNING: These commands will permanently delete tables!")
    print("⚠️  Only run after careful review and backup!")
    
    safe_to_delete = [t['name'] for t in categories['empty_no_dependencies'] 
                      if any(pattern in t['name'].lower() for pattern in ['temp', 'test', 'old'])]
    
    if safe_to_delete:
        print("\nPotentially safe to delete (temp/test/old tables):")
        for table in safe_to_delete:
            print(f"-- DROP TABLE {table};")
    
    print("\nTo delete ALL empty tables with no dependencies (DANGEROUS!):")
    print("-- Run this only after careful review:")
    print("/*")
    for table in categories['empty_no_dependencies']:
        print(f"DROP TABLE {table['name']};")
    print("*/")
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. Before deleting any tables:
   - Make a backup: cp data/output/pnl/pnl_tracker.db data/output/pnl/pnl_tracker.db.backup
   - Review the purpose of each table
   - Check if any code references these tables
   
2. Start with obviously safe deletions:
   - Tables with 'temp' or 'test' in the name
   - Old backup tables that are no longer needed
   
3. For tables with unknown purposes:
   - Search the codebase for references
   - Check if they're created by specific processes
   - Consider keeping them if unsure
   
4. Never delete:
   - Tables with data (populated tables)
   - Tables with foreign key relationships
   - Core business tables (trades, positions, pnl components)
""")

if __name__ == "__main__":
    main() 