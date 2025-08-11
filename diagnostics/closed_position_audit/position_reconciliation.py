"""
Diagnostic Script: Reconcile daily_positions vs realized trades
This will identify discrepancies between what's shown and what's actually traded
"""
import sqlite3
import pandas as pd
from datetime import datetime

def reconcile_positions(db_path='trades.db'):
    """Compare daily_positions closed counts vs actual realized trades"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("POSITION RECONCILIATION REPORT")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    for method in ['fifo', 'lifo']:
        print(f"\n### {method.upper()} Method Analysis ###")
        
        # Get daily positions data
        daily_query = f"""
        SELECT 
            date,
            symbol,
            closed_position,
            realized_pnl
        FROM daily_positions
        WHERE method = '{method}'
        ORDER BY date DESC, symbol
        """
        
        daily_df = pd.read_sql_query(daily_query, conn)
        
        # Get actual realized trades grouped by date and symbol
        realized_query = f"""
        SELECT 
            DATE(timestamp) as date,
            symbol,
            SUM(quantity) as actual_closed,
            SUM(realized_pnl) as actual_pnl,
            COUNT(*) as trade_count
        FROM realized_{method}
        GROUP BY DATE(timestamp), symbol
        ORDER BY date DESC, symbol
        """
        
        realized_df = pd.read_sql_query(realized_query, conn)
        
        # Merge the two datasets
        comparison = pd.merge(
            daily_df,
            realized_df,
            on=['date', 'symbol'],
            how='outer',
            suffixes=('_daily', '_realized')
        )
        
        # Calculate discrepancies
        comparison['position_discrepancy'] = comparison['closed_position'].fillna(0) - comparison['actual_closed'].fillna(0)
        comparison['pnl_discrepancy'] = comparison['realized_pnl'].fillna(0) - comparison['actual_pnl'].fillna(0)
        
        # Filter to show only discrepancies
        discrepancies = comparison[comparison['position_discrepancy'] != 0]
        
        if len(discrepancies) > 0:
            print(f"\n⚠️  FOUND {len(discrepancies)} POSITION DISCREPANCIES!")
            print("\nDiscrepancy Details:")
            print("-" * 120)
            print(f"{'Date':<12} {'Symbol':<15} {'Daily Pos':<10} {'Actual':<10} {'Diff':<10} {'Trade Count':<12} {'PnL Diff':<10}")
            print("-" * 120)
            
            for idx, row in discrepancies.iterrows():
                print(f"{row['date']:<12} {row['symbol']:<15} "
                      f"{row['closed_position']:>10.0f} {row['actual_closed']:>10.0f} "
                      f"{row['position_discrepancy']:>10.0f} {row['trade_count']:>12.0f} "
                      f"{row['pnl_discrepancy']:>10.2f}")
            
            # Summary statistics
            print("\nSummary:")
            print(f"Total position over-count: {discrepancies['position_discrepancy'].sum():.0f}")
            print(f"Total PnL discrepancy: ${discrepancies['pnl_discrepancy'].sum():.2f}")
            print(f"Affected symbol-days: {len(discrepancies)}")
            
            # Check which dates have the most issues
            date_summary = discrepancies.groupby('date').agg({
                'position_discrepancy': 'sum',
                'symbol': 'count'
            }).rename(columns={'symbol': 'affected_symbols'})
            
            print("\nDiscrepancies by date:")
            print(date_summary.sort_values('position_discrepancy', ascending=False))
            
        else:
            print("✅ No position discrepancies found")
    
    # Check for any symbols in daily_positions not in realized tables
    orphan_query = """
    SELECT DISTINCT 
        dp.date,
        dp.symbol,
        dp.method,
        dp.closed_position
    FROM daily_positions dp
    LEFT JOIN (
        SELECT DISTINCT symbol, DATE(timestamp) as date FROM realized_fifo
        UNION
        SELECT DISTINCT symbol, DATE(timestamp) as date FROM realized_lifo
    ) r ON dp.symbol = r.symbol AND dp.date = r.date
    WHERE r.symbol IS NULL
      AND dp.closed_position > 0
    """
    
    orphans = pd.read_sql_query(orphan_query, conn)
    if len(orphans) > 0:
        print("\n⚠️  Found daily_positions entries with no corresponding realized trades:")
        print(orphans)
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    reconcile_positions()