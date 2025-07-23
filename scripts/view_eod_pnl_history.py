#!/usr/bin/env python3
"""View EOD P&L history for 2pm-to-2pm periods."""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def view_eod_pnl_history():
    """Display EOD P&L history from the database."""
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tyu5_eod_pnl_history'
    """)
    if not cursor.fetchone():
        print("❌ Table 'tyu5_eod_pnl_history' does not exist yet.")
        print("   It will be created when the first EOD snapshot is taken at 4pm.")
        return
    
    # Get all EOD P&L records
    query = """
        SELECT 
            snapshot_date,
            symbol,
            realized_pnl,
            unrealized_pnl_settle as unrealized_pnl,
            total_daily_pnl,
            position_quantity as open_quantity,
            NULL as avg_entry_price,
            settlement_price,
            pnl_period_start,
            pnl_period_end,
            created_at
        FROM tyu5_eod_pnl_history
        ORDER BY snapshot_date DESC, symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No EOD P&L history found yet.")
        print("EOD snapshots are taken at 4pm CDT when settlement prices are available.")
        return
    
    print("=" * 80)
    print("EOD P&L HISTORY (2pm-to-2pm periods)")
    print("=" * 80)
    
    # Group by date
    for date in df['snapshot_date'].unique():
        date_df = df[df['snapshot_date'] == date]
        total_row = date_df[date_df['symbol'] == 'TOTAL'].iloc[0] if 'TOTAL' in date_df['symbol'].values else None
        
        print(f"\n📅 Date: {date}")
        if total_row is not None and pd.notna(total_row['pnl_period_start']):
            print(f"   Period: {total_row['pnl_period_start']} to {total_row['pnl_period_end']}")
        
        print("\n   Symbol | Realized | Unrealized | Total Daily | Open Qty | Avg Entry | Settle")
        print("   " + "-" * 70)
        
        # Show individual symbols first
        for _, row in date_df.iterrows():
            if row['symbol'] != 'TOTAL':
                avg_entry = row['avg_entry_price'] if pd.notna(row['avg_entry_price']) else 0
                settle = row['settlement_price'] if pd.notna(row['settlement_price']) else 0
                print(f"   {row['symbol']:6} | ${row['realized_pnl']:8,.2f} | ${row['unrealized_pnl']:9,.2f} | "
                      f"${row['total_daily_pnl']:11,.2f} | {row['open_quantity']:8.0f} | "
                      f"{avg_entry:9.4f} | {settle:7.4f}")
        
        # Show total
        if total_row is not None:
            print("   " + "-" * 70)
            print(f"   {'TOTAL':6} | ${total_row['realized_pnl']:8,.2f} | ${total_row['unrealized_pnl']:9,.2f} | "
                  f"${total_row['total_daily_pnl']:11,.2f}")
    
    conn.close()

def view_pnl_components_by_period():
    """View P&L components aggregated by settlement period."""
    conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
    
    print("\n" + "=" * 80)
    print("P&L COMPONENTS BY SETTLEMENT PERIOD")
    print("=" * 80)
    
    # Use the view if it exists
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' AND name='tyu5_eod_pnl_by_period'
    """)
    
    if cursor.fetchone():
        # Use the view
        query = """
            SELECT * FROM tyu5_eod_pnl_by_period
            ORDER BY start_settlement_key DESC, symbol
        """
    else:
        # Direct query
        query = """
            SELECT
                start_settlement_key,
                end_settlement_key,
                symbol,
                SUM(pnl_amount) as period_pnl,
                COUNT(*) as component_count,
                GROUP_CONCAT(DISTINCT component_type) as component_types
            FROM tyu5_pnl_components
            WHERE start_settlement_key IS NOT NULL
              AND end_settlement_key IS NOT NULL
            GROUP BY start_settlement_key, end_settlement_key, symbol
            ORDER BY start_settlement_key DESC, symbol
        """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No P&L components found.")
        return
    
    print("\nSettlement Period P&L:")
    print("Start Key    | End Key      | Symbol | P&L         | Components")
    print("-" * 70)
    
    current_period = None
    period_total = 0
    
    for _, row in df.iterrows():
        period_key = f"{row['start_settlement_key']} -> {row['end_settlement_key']}"
        
        if current_period != period_key:
            if current_period is not None:
                print(f"{'':14} {'':14} {'TOTAL':6} | ${period_total:10,.2f}")
                print("-" * 70)
            current_period = period_key
            period_total = 0
        
        print(f"{row['start_settlement_key']} | {row['end_settlement_key']} | "
              f"{row['symbol']:6} | ${row['period_pnl']:10,.2f} | {row['component_types']}")
        period_total += row['period_pnl']
    
    # Print last period total
    if current_period is not None:
        print(f"{'':14} {'':14} {'TOTAL':6} | ${period_total:10,.2f}")
    
    conn.close()

if __name__ == "__main__":
    view_eod_pnl_history()
    view_pnl_components_by_period() 