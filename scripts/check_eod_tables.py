import sqlite3

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

# Check if EOD history table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tyu5_eod_pnl_history'")
eod_exists = cursor.fetchone() is not None
print(f"tyu5_eod_pnl_history table exists: {eod_exists}")

if eod_exists:
    cursor.execute("SELECT COUNT(*) FROM tyu5_eod_pnl_history")
    count = cursor.fetchone()[0]
    print(f"  - Records: {count}")

# Check P&L components
cursor.execute("SELECT COUNT(*) FROM tyu5_pnl_components")
comp_count = cursor.fetchone()[0]
print(f"\ntyu5_pnl_components table: {comp_count} records")

if comp_count > 0:
    cursor.execute("""
        SELECT DISTINCT start_settlement_key, end_settlement_key 
        FROM tyu5_pnl_components 
        WHERE start_settlement_key IS NOT NULL
        ORDER BY start_settlement_key
    """)
    print("\nUnique settlement periods in components:")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}")

# Check open lot snapshots
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tyu5_open_lot_snapshots'")
snapshots_exists = cursor.fetchone() is not None
print(f"\ntyu5_open_lot_snapshots table exists: {snapshots_exists}")

if snapshots_exists:
    cursor.execute("SELECT COUNT(*) FROM tyu5_open_lot_snapshots")
    snap_count = cursor.fetchone()[0]
    print(f"  - Records: {snap_count}")

conn.close() 