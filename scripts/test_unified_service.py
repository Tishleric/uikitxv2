#!/usr/bin/env python
"""Test the UnifiedPnLService to see if it returns data."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_calculator.data_aggregator import PnLDataAggregator

# Initialize service with the correct database
service = UnifiedPnLService(
    db_path="data/output/pnl/pnl_tracker.db",
    trade_ledger_dir="data/input/trade_ledger",
    price_directories=[
        "data/input/market_prices/futures",
        "data/input/market_prices/options"
    ]
)

# Initialize aggregator
aggregator = PnLDataAggregator(service)

print("Testing UnifiedPnLService...")
print("="*60)

# Test 1: Get open positions
print("\n1. Open Positions:")
positions = service.get_open_positions()
print(f"   Found {len(positions)} positions")
if positions:
    for pos in positions[:3]:
        print(f"   - {pos}")

# Test 2: Get trade history
print("\n2. Trade History:")
trades = service.get_trade_history(limit=5)
print(f"   Found {len(trades)} trades")
if trades:
    for trade in trades[:3]:
        print(f"   - {trade.get('trade_time', 'N/A')}: {trade.get('symbol', 'N/A')} {trade.get('quantity', 0)} @ {trade.get('price', 0)}")

# Test 3: Get daily P&L
print("\n3. Daily P&L History:")
daily_pnl = service.get_daily_pnl_history()
print(f"   Found {len(daily_pnl)} days")
if daily_pnl:
    for day in daily_pnl[:3]:
        print(f"   - {day}")

# Test 4: Get summary metrics
print("\n4. Summary Metrics:")
metrics = aggregator.get_summary_metrics()
for key, value in metrics.items():
    print(f"   {key}: {value}")

# Test 5: Check if positions table is populated
print("\n5. Direct Database Check:")
import sqlite3
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM positions")
pos_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM processed_trades")
trade_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM pnl_snapshots")
snapshot_count = cursor.fetchone()[0]
conn.close()

print(f"   positions table: {pos_count} rows")
print(f"   processed_trades table: {trade_count} rows")
print(f"   pnl_snapshots table: {snapshot_count} rows")

print("\n" + "="*60)
print("Test complete!") 