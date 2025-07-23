#!/usr/bin/env python3
"""
One-time migration script to fix mislabeled settle_to_exit components.

This script identifies open positions that have settle_to_exit components
and relabels them as settle_to_current to accurately reflect their status.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz

def analyze_components():
    """Analyze current P&L components to identify issues."""
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    
    print("=== Analyzing P&L Components ===\n")
    
    # Get all settle_to_exit components
    query = """
        SELECT 
            c.lot_id,
            c.symbol,
            c.component_type,
            c.start_time,
            c.end_time,
            c.pnl_amount,
            p.Net_Quantity as position_qty
        FROM tyu5_pnl_components c
        LEFT JOIN tyu5_positions p ON c.symbol = p.Symbol
        WHERE c.component_type = 'settle_to_exit'
        ORDER BY c.symbol, c.start_time
    """
    
    df = pd.read_sql_query(query, conn)
    print(f"Found {len(df)} settle_to_exit components")
    
    if not df.empty:
        print("\nComponents with open positions (should be settle_to_current):")
        open_positions = df[df['position_qty'] > 0]
        print(open_positions[['symbol', 'start_time', 'end_time', 'position_qty']].to_string(index=False))
    
    conn.close()
    return df

def migrate_components(dry_run=True):
    """
    Migrate mislabeled components from settle_to_exit to settle_to_current.
    
    Args:
        dry_run: If True, show what would be changed without making changes
    """
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    cursor = conn.cursor()
    
    chicago_tz = pytz.timezone('America/Chicago')
    current_time = datetime.now(chicago_tz)
    
    # Identify components to migrate
    # These are settle_to_exit components where:
    # 1. The position is still open (Net_Quantity != 0)
    # 2. The end_time is recent (within last 48 hours)
    
    identify_query = """
        SELECT 
            c.lot_id,
            c.symbol,
            c.end_time,
            p.Net_Quantity
        FROM tyu5_pnl_components c
        INNER JOIN tyu5_positions p ON c.symbol = p.Symbol
        WHERE c.component_type = 'settle_to_exit'
          AND p.Net_Quantity != 0
          AND datetime(c.end_time) > datetime('now', '-2 days')
    """
    
    components_to_migrate = pd.read_sql_query(identify_query, conn)
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Found {len(components_to_migrate)} components to migrate")
    
    if not components_to_migrate.empty:
        print("\nComponents to be migrated:")
        print(components_to_migrate.to_string(index=False))
        
        if not dry_run:
            # Perform the migration
            update_query = """
                UPDATE tyu5_pnl_components
                SET component_type = 'settle_to_current'
                WHERE lot_id = ? AND component_type = 'settle_to_exit'
            """
            
            for _, comp in components_to_migrate.iterrows():
                cursor.execute(update_query, (comp['lot_id'],))
            
            conn.commit()
            print(f"\n✓ Successfully migrated {len(components_to_migrate)} components")
        else:
            print("\n[DRY RUN] No changes made. Run with --apply to perform migration.")
    else:
        print("\nNo components need migration.")
    
    conn.close()

def verify_migration():
    """Verify the migration was successful."""
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    
    # Check for any remaining problematic components
    query = """
        SELECT 
            COUNT(*) as count,
            component_type
        FROM tyu5_pnl_components c
        INNER JOIN tyu5_positions p ON c.symbol = p.Symbol
        WHERE p.Net_Quantity != 0
        GROUP BY component_type
    """
    
    df = pd.read_sql_query(query, conn)
    print("\n=== Post-Migration Verification ===")
    print("\nComponent types for open positions:")
    print(df.to_string(index=False))
    
    conn.close()

def main():
    """Run the migration process."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate mislabeled settle_to_exit components to settle_to_current'
    )
    parser.add_argument(
        '--apply', 
        action='store_true', 
        help='Apply the migration (default is dry run)'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze components without migrating'
    )
    
    args = parser.parse_args()
    
    print("P&L Component Migration Tool")
    print("=" * 60)
    
    # Always start with analysis
    analyze_components()
    
    if not args.analyze_only:
        # Perform migration
        print("\n" + "=" * 60)
        migrate_components(dry_run=not args.apply)
        
        if args.apply:
            # Verify if migration was applied
            verify_migration()
    
    print("\nComplete.")

if __name__ == "__main__":
    main() 