"""Recreate PnL database cleanly, removing old data."""

import os
import sys
import shutil
from datetime import datetime
import sqlite3

# Add project root to path
sys.path.append('.')

# Database path
db_path = "data/output/pnl/pnl_tracker.db"
backup_dir = "data/output/pnl/backups"

# Create backup directory if it doesn't exist
os.makedirs(backup_dir, exist_ok=True)

# Backup the existing database
if os.path.exists(db_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"pnl_tracker_backup_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    print(f"Backed up existing database to: {backup_path}")
    
    # Remove the old database
    os.remove(db_path)
    print(f"Removed old database: {db_path}")
else:
    print("No existing database found to backup")

# Create fresh database with schema
from lib.trading.pnl_calculator.storage import PnLStorage

print("\nCreating fresh database...")
storage = PnLStorage(db_path)

# Verify it's empty
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f"\nCreated tables: {[t[0] for t in tables]}")

# Check if positions table is empty
cursor.execute("SELECT COUNT(*) FROM positions")
pos_count = cursor.fetchone()[0]
print(f"Positions count: {pos_count}")

# Check if processed_trades is empty
cursor.execute("SELECT COUNT(*) FROM processed_trades")
trade_count = cursor.fetchone()[0]
print(f"Processed trades count: {trade_count}")

conn.close()

print("\nDatabase recreated successfully!")
print("The new database is ready for fresh data processing.") 