import sys
sys.path.append('.')

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_calculator.data_aggregator import PnLDataAggregator

# Initialize services
service = UnifiedPnLService(
    db_path="data/output/pnl/pnl_tracker.db",
    trade_ledger_dir="data/input/trade_ledger",
    price_directories=[
        "data/input/market_prices/futures",
        "data/input/market_prices/options"
    ]
)

aggregator = PnLDataAggregator(service)

# Test 1: Get open positions from service
print("Test 1: Getting open positions from UnifiedPnLService...")
positions = service.get_open_positions()
print(f"Found {len(positions)} positions")
if positions:
    print(f"Sample position: {positions[0]}")

# Test 2: Format positions for display
print("\nTest 2: Formatting positions for display...")
positions_df = aggregator.format_positions_for_display(positions)
print(f"Formatted DataFrame shape: {positions_df.shape}")
print(f"Columns: {list(positions_df.columns)}")
if not positions_df.empty:
    print(f"\nFirst few rows:")
    print(positions_df.head())

# Test 3: Convert to dict records (as used by Dash DataTable)
print("\nTest 3: Converting to dict records for Dash...")
records = positions_df.to_dict('records')
print(f"Number of records: {len(records)}")
if records:
    print(f"Sample record: {records[0]}")

# Test 4: Check if total_pnl column exists
print("\nTest 4: Checking for total_pnl column...")
if positions:
    sample = positions[0]
    print(f"Position keys: {list(sample.keys())}")
    if 'total_pnl' not in sample:
        print("WARNING: total_pnl key missing from positions!")
        # Check if it should be calculated
        if 'total_realized_pnl' in sample and 'unrealized_pnl' in sample:
            print(f"But we have: total_realized_pnl={sample.get('total_realized_pnl')}, unrealized_pnl={sample.get('unrealized_pnl')}")
            print("Need to calculate total_pnl = total_realized_pnl + unrealized_pnl") 