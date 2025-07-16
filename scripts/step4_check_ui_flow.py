"""Step 4: Check complete data flow to UI."""

import sys
sys.path.append('.')
from datetime import datetime

print("=== STEP 4: CHECKING DATA FLOW TO UI ===")
print(f"Time: {datetime.now()}\n")

# 1. Check raw database
print("1. RAW DATABASE CHECK:")
import sqlite3
conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM positions")
db_positions = cursor.fetchone()[0]
print(f"   ✓ Positions in DB: {db_positions}")
conn.close()

# 2. Check UnifiedPnLService
print("\n2. UNIFIED SERVICE CHECK:")
from lib.trading.pnl_calculator.unified_service import UnifiedPnLService

service = UnifiedPnLService(
    db_path="data/output/pnl/pnl_tracker.db",
    trade_ledger_dir="data/input/trade_ledger",
    price_directories=["data/input/market_prices/futures", "data/input/market_prices/options"]
)

positions = service.get_open_positions()
print(f"   ✓ Service returned: {len(positions)} positions")

# 3. Check DataAggregator
print("\n3. DATA AGGREGATOR CHECK:")
from lib.trading.pnl_calculator.data_aggregator import PnLDataAggregator

aggregator = PnLDataAggregator(service)
positions_df = aggregator.format_positions_for_display(positions)
print(f"   ✓ Aggregator formatted: {len(positions_df)} positions")
print(f"   Columns: {list(positions_df.columns)}")

# 4. Check Controller
print("\n4. CONTROLLER CHECK:")
from apps.dashboards.pnl_v2.controller import PnLDashboardController

controller = PnLDashboardController()
positions_data = controller.get_positions_data()
print(f"   ✓ Controller returned: {positions_data['count']} positions")

# 5. Show sample data at each level
if positions:
    print("\n5. SAMPLE DATA AT EACH LEVEL:")
    
    print("\n   A. Raw position from service:")
    sample = positions[0]
    for key, value in sample.items():
        print(f"      {key}: {value}")
    
    print("\n   B. After aggregator formatting:")
    if not positions_df.empty:
        formatted = positions_df.iloc[0].to_dict()
        for key, value in formatted.items():
            print(f"      {key}: {value}")
    
    print("\n   C. From controller (ready for UI):")
    if positions_data['data']:
        ui_data = positions_data['data'][0]
        for key, value in ui_data.items():
            print(f"      {key}: {value}")
    else:
        print("      ❌ NO DATA FROM CONTROLLER!")

# 6. Diagnose any breaks
print("\n6. DIAGNOSIS:")
if db_positions > 0 and len(positions) == 0:
    print("   ❌ BREAK: Database has positions but service returns none")
    print("      → Check UnifiedPnLService.get_open_positions()")
elif len(positions) > 0 and len(positions_df) == 0:
    print("   ❌ BREAK: Service has positions but aggregator returns none")
    print("      → Check DataAggregator.format_positions_for_display()")
elif len(positions_df) > 0 and positions_data['count'] == 0:
    print("   ❌ BREAK: Aggregator has positions but controller returns none")
    print("      → Check PnLDashboardController.get_positions_data()")
elif positions_data['count'] > 0:
    print("   ✅ Data flows correctly through all layers!")
    print(f"   → {positions_data['count']} positions should appear in UI")
else:
    print("   ⚠️  No positions at any level - need to process trades first")

print("\n✅ STEP 4 COMPLETE") 