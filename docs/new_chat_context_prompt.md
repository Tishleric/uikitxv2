# Context for UIKitXv2 Trading System File Watchers and Pipelines

I need help understanding and working with the file watchers and processing pipelines in the UIKitXv2 trading system. Below is the current system state and architecture.

## Current System Architecture

### File Watchers (5 Active)
1. **Market Price File Monitor** - Watches for futures/options CSV files at 2pm/4pm
2. **Spot Risk Watcher** - Processes Actant spot risk files with Greeks
3. **PNL Pipeline Watcher** - Central orchestrator monitoring trades, prices, and spot risk
4. **EOD P&L Monitor** - Captures 4pm settlement snapshots
5. **Lot Snapshot Monitor** - Takes 2pm position snapshots

### Processing Pipelines
1. **TYU5 P&L Pipeline**: Trade preprocessing → P&L calculation → Database storage
2. **FULLPNL Builder**: Merges TYU5 positions with spot risk Greeks
3. **EOD Snapshot**: Aggregates P&L components for daily history

### Key Directories
- Input trades: `data/input/trade_ledger/trades_*.csv`
- Input prices: `data/input/market_prices/futures/` and `/options/`
- Input spot risk: `data/input/actant_spot_risk/`
- Output databases: `data/output/pnl/pnl_tracker.db`, `data/output/market_prices/market_prices.db`

### Important Behavior
- Watchers mark existing files as "processed" on startup to prevent reprocessing
- Only NEW or MODIFIED files after startup trigger processing
- All watchers use 10-second debouncing to prevent rapid triggers
- P&L periods run 2pm-to-2pm Chicago time

### Recent Issues Fixed
1. **DataFrame attribute error**: Changed `position_details.Symbol` to `position_details['Symbol']` in BreakdownGenerator
2. **Timestamp serialization**: Added pandas Timestamp to string conversion for SQLite compatibility
3. **Schema mismatch**: Removed non-existent `created_at` column from P&L components insert

### Available Scripts
- `scripts/run_all_watchers.py` - Start all watchers (recommended)
- `scripts/force_pnl_reprocessing.py` - Force reprocess existing files
- `scripts/check_pnl_processing_status.py` - View current system state
- `scripts/reset_pnl_processing.py` - Clear all data and reset

## Questions/Tasks
[Your specific questions or tasks here]

## Additional Context
The system is currently in production with active monitoring. The FRGMonitor dashboard has two tabs: FULLPNL (real-time positions) and Historic EOD PnL (daily P&L history).

Full documentation available at: `docs/file_watchers_and_pipelines_context.md` 