import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

tables = ['tyu5_trades', 'tyu5_positions', 'tyu5_summary', 
          'tyu5_risk_matrix', 'tyu5_position_breakdown', 
          'tyu5_pnl_components', 'tyu5_runs']

for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} rows')

conn.close() 