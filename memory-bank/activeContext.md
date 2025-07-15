# Active Context

## Current Focus: P&L System Phase 2 - Data Pipeline Infrastructure

### Just Completed
- ✅ Trade Preprocessor Module (`lib/trading/pnl_calculator/trade_preprocessor.py`)
  - Processes raw trade files with symbol translation
  - Tracks file changes to avoid unnecessary reprocessing
  - Outputs to `data/output/trade_ledger_processed/`
  
- ✅ Trade File Watcher (`lib/trading/pnl_calculator/trade_file_watcher.py`)
  - Monitors trade ledger directory for changes
  - Handles growing files (reexported throughout day)
  - Implements 4pm CDT cutover logic

### Key Implementation Details
- Trade files grow throughout the day as they're reexported
- At 4pm CDT, system switches to next day's file
- Preprocessor tracks file size/mtime to detect changes
- Processed files preserve original trade date in filename

### Test Results
- Symbol translation: 100% working
- File change detection: Working correctly
- SOD detection: 8 positions found in test
- Expiry detection: 2 expiries found in test

### Next Steps
1. **Create Price Router** (phase2-price-router)
   - Integrate with existing price file selector
   - Route prices based on time windows
   - Handle fallback logic

2. **Begin Database Schema** (phase2-db-schema)
   - Design tables for trades, positions, P&L
   - Plan state persistence strategy
   - Consider audit requirements

### Running the Preprocessor
```bash
# Process existing files only
python scripts/run_trade_preprocessor.py --process-only

# Run in watch mode (continuous monitoring)
python scripts/run_trade_preprocessor.py

# Test the preprocessor
python scripts/test_trade_preprocessor.py
```

### File Locations
- Input: `data/input/trade_ledger/trades_YYYYMMDD.csv`
- Output: `data/output/trade_ledger_processed/trades_YYYYMMDD_processed.csv`
- State tracking: `data/output/trade_ledger_processed/.processing_state.json` 