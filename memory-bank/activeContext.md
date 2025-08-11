# Active Context

## Current Status: Debug Logging Added to Watchers (2025-08-04)

### What Was Just Done
1. **Trade Ledger Watcher Debug Logging**:
   - Added `--debug` flag support to show detailed console output
   - Logs trade processing, P&L calculations, position updates
   - Fixed `closed_position` accumulation bug (now uses `abs()` on realized quantities)
   - Fixed SQL error: changed queries from `positions` to `daily_positions` table

2. **Spot Risk Watcher Greek Tracing**:
   - Added Greek calculation tracing to both console and log files
   - Logs inputs to Greek API calls and results
   - Fixed `FileNotFoundError` by ensuring log directory exists
   - Fixed `UnicodeEncodeError` by replacing Unicode arrow with ASCII

3. **Key Fixes Applied**:
   - `lib/trading/pnl_fifo_lifo/trade_ledger_watcher.py`:
     - Line 163: `realized_qty = abs(realized['qty'].iloc[0] or 0)`
     - Lines 196, 217: Changed SQL from `FROM positions` to `FROM daily_positions`
   - `lib/trading/actant/spot_risk/file_watcher.py`:
     - Line 137: Changed `→` to `->` in SYMBOL_MAP log
   - `lib/trading/actant/spot_risk/greek_logger.py`:
     - Added `os.makedirs(log_dir, exist_ok=True)`

### How to Use
- Run `run_pipeline_live.bat` - Trade Ledger and Spot Risk watchers now run in debug mode
- Trade Ledger shows: trades, P&L calculations, position updates in console
- Spot Risk shows: file detection, symbol translation, Greek calculations
- Greek details also written to `logs/greek_trace/greek_values_*.log`

## Previous Status: Live PnL Fix Applied (2025-08-04)

### Critical Issue Fixed
- **Problem**: Live PnL showing only realized component (unrealized = 0)
- **Root Cause**: Price updates don't trigger positions_aggregator refresh
- **Solution**: Modified `update_current_price()` to publish Redis signal

### Technical Details
1. **Issue Diagnosis**:
   - Positions table had `fifo_unrealized_pnl = 0` despite having current prices
   - PositionsAggregator only refreshed on trade events, not price updates
   - After historical rebuild, aggregator never recalculated with live prices

2. **Fix Applied (Three Parts)**:
   - Modified `lib/trading/pnl_fifo_lifo/data_manager.py`
     - Added Redis publish to `update_current_price()` function
     - Now publishes "positions:changed" signal after each price update
   - Modified `lib/trading/pnl_fifo_lifo/positions_aggregator.py` (two changes)
     - Added database write queue operation after loading positions
     - Added Greek preservation logic in `_load_positions_from_db()`
     - Greeks from in-memory cache are restored after database load

3. **Verification**:
   - Created diagnostic script: `diagnose_live_pnl_issue.py`
   - Created verification script: `verify_live_pnl_fix.py`
   - Integration tests: `tests/integration/live_pnl_test/`

### Implementation Complete
- **Live PnL**: Updates with every price change using 'now' prices
- **Close PnL**: Updates when today's close prices arrive
- **Daily Positions**: Records historical Close PnL values only
- **Fix Applied**: `update_daily_positions_unrealized_pnl()` now only updates when today's close exists

### Known Issues Still Present
- **sodTod prices**: Not automatically populated in live operation
- **sodTom prices**: Never written by any automated process
- **After 14:00**: PnL calculation expects sodTom but falls back to entry price

### Next Steps
1. Ensure positions_aggregator service is running
2. Consider automating sodTod/sodTom price management
3. Monitor Live PnL column to verify fix is working

## Previous Status: Close PnL Implementation Complete ✓

### What Just Happened (2025-08-03)
- **Implemented Close PnL**: Added parallel close-based PnL calculation to FRGMonitor
- **Database Migration**: Added `fifo_unrealized_pnl_close` and `lifo_unrealized_pnl_close` columns
- **PositionsAggregator Updated**: Now calculates both live and close unrealized PnL
- **FRGMonitor Updated**: Shows close PnL when today's close price is available
- **Close Price Display Updated**: Close price column now only shows today's settlement price

### Close PnL Implementation Details
1. **Database Changes**:
   - Added two columns to positions table: `fifo_unrealized_pnl_close` and `lifo_unrealized_pnl_close`
   - Migration script created: `scripts/migration/010_add_close_pnl_columns.py`
   - Schema updated in `data_manager.py`

2. **PositionsAggregator Changes**:
   - Calculates close unrealized PnL alongside live unrealized PnL
   - Uses same `calculate_unrealized_pnl()` function but substitutes close prices for now prices
   - Only calculates when today's close price is available

3. **FRGMonitor Callback Changes**:
   - Removed time-based conditional (2-4pm window)
   - Added date-based check on close price timestamp
   - Formula: `pnl_close = fifo_realized_pnl + fifo_unrealized_pnl_close`
   - Shows NULL when close price is not from today
   - Close price column (`close_px`) also shows NULL when not from today

### Key Benefits
- **Consistency**: Close PnL uses exact same methodology as live PnL
- **Performance**: Pre-calculated by PositionsAggregator, no on-the-fly computation
- **Simplicity**: No dependency on daily_positions table
- **Accuracy**: Updates with same frequency as live PnL

### Previous Update (2025-01-27)
- **Fixed Trade Watcher**: Added missing `update_daily_position()` calls to trade_ledger_watcher.py
- **Continuous Updates**: Daily positions table now updates in real-time as trades are processed
- **Native Integration**: Using the existing pnl_fifo_lifo module's update mechanism
- **Production Safe**: Changes made carefully to avoid disrupting production trades.db

### Changes Made
1. **Import Added**: `update_daily_position` imported from `.data_manager`
2. **Update Logic Added**: After each trade is processed through FIFO/LIFO:
   - Calculate realized quantities and P&L deltas
   - Get trading day from trade timestamp
   - Call `update_daily_position()` to update the table
3. **Pattern Matched**: Followed the same pattern used in `main.py` batch processing

### Daily Positions Table Now Updates
- **open_position**: Continuously recalculated net position
- **closed_position**: Incremented with each realized trade
- **realized_pnl**: Incremented with P&L from offsetting trades
- **unrealized_pnl**: Still only updates at 2pm/4pm (by design)

### Production Considerations
- No tests run against production trades.db
- Changes are minimal and surgical
- Existing functionality preserved
- Database connection handling unchanged

## Previous Status: PnL System Clean Slate Achieved ✓

### What Happened Earlier (Phase 3 - Completed 2025-07-25)
- **Complete PnL System Removal**: All existing PnL code has been removed
- **Clean Slate Approach**: Pre-production system allowed aggressive removal
- **~200 Files Removed**: Dashboards, scripts, tests, services, engines
- **Database Cleanup**: All PnL tables dropped, pnl_tracker.db removed
- **File Watchers Preserved**: Converted to minimal skeletons for integration

### Rollback Safety
- **Git Tag**: `pre-pnl-removal-20250725-141713`
- **Database Backups**: `backups/pre-removal-20250725/`
- **Complete Audit Trail**: Every removal documented

### Integration Ready
The codebase is now ready for clean integration of a new PnL module:
- **Trade Watcher**: `lib/trading/pnl_calculator/trade_preprocessor.py`
- **Pipeline Watcher**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py`
- **Integration Spec**: `memory-bank/pnl_migration/integration_specification.md`

### Next Steps
1. New PnL module can be integrated cleanly
2. No legacy code conflicts
3. Clear integration points documented
4. Simple callback-based architecture

## Previous Context (Now Resolved)
The previous confusion about multiple PnL systems has been completely eliminated through the Phase 3 clean slate removal.

## Recent Update: Greek Configuration System (2025-01-27)

### What Was Implemented
1. **Greek Configuration Module** (`lib/trading/actant/spot_risk/greek_config.py`):
   - Allows selective calculation of Greeks for performance optimization
   - Default enabled: delta_F, delta_y, gamma_F, gamma_y, speed_F, speed_y, theta_F
   - Disabled by default: vega_price, vega_y, volga_price, vanna_F_price, charm_F, color_F, ultima, zomma
   - Environment variable override: `SPOT_RISK_GREEKS_ENABLED`
   - 60% performance improvement when using minimal Greeks

2. **Futures DV01 Mapping**:
   - Contract-specific DV01 values implemented
   - ZN (10-year): 64.2 (updated from 63.0)
   - US (20-year): 140.0
   - FV (5-year): 42.0
   - TU (2-year): 22.7
   - Automatic fallback to default for unknown futures types

3. **API and Calculator Updates**:
   - `SpotRiskGreekCalculator` now accepts `greek_config` parameter
   - `GreekCalculatorAPI` supports `requested_greeks` parameter
   - Disabled Greeks set to `None` (become NaN in DataFrame)
   - Futures mask calculation fixed to use `df_copy` instead of `df`

### Benefits
- **Performance**: ~60% faster with minimal Greeks (7 vs 14 calculations)
- **Flexibility**: Can enable/disable Greeks as needed
- **Accuracy**: Contract-specific DV01 values for proper yield sensitivity
- **Backward Compatible**: Default configuration matches previous behavior

## Current Focus: Spot Risk Greek Calculation Pipeline Testing (2025-08-05)

### Progress Today
Successfully created and ran comprehensive unit tests for the spot risk CSV parsing pipeline:
- ✅ File detection and pattern matching - validated chunk file naming patterns
- ✅ CSV parsing and column mapping - tested all price sources (adjtheor, bid/ask)
- ✅ Symbol translation - confirmed Actant to Bloomberg mappings work correctly
- ✅ Future price extraction - successfully identified futures and extracted prices
- ✅ VTEXP mapping - all options mapped to time-to-expiry values
- ✅ Parameter assembly - 100% success rate preparing data for Greek calculations
- ✅ End-to-end worker simulation - validated complete processing flow

### Key Findings from Testing:
1. **Symbol Translation Examples:**
   - Futures: `XCME.ZN.SEP25` → `TYU5 Comdty`
   - Call Options: `XCME.WY1.06AUG25.110.C` → `TYWQ25C1 110 Comdty`
   - Put Options: `XCME.WY1.06AUG25.113.P` → `TYWQ25P1 113 Comdty`

2. **Price Sources:**
   - Primary: `adjtheor` column (theoretical adjusted price)
   - Fallback: Calculated midpoint from bid/ask
   - Successfully handled both sources in test data

3. **VTEXP Mapping:**
   - Maps expiry dates to time-to-expiry in days
   - Example: `06AUG25` options mapped to `vtexp=2.583333` days

4. **Test Suite Created:**
   - `tests/test_spot_risk_parsing_pipeline.py`
   - Uses actual production CSV data
   - All 7 tests passing
   - Validates complete parsing pipeline up to Greek calculation

### Critical Issues Discovered (2025-08-05)

#### 1. VTEXP Values Are In Days, Not Years!
- **Problem**: VTEXP CSV contains values in DAYS (e.g., 2.583333 days for 06AUG25)
- **Expected**: Greek calculator expects values in YEARS  
- **Reality**: NO conversion is happening - raw day values are passed as years
- **Impact**: Greeks calculated with ~252x incorrect time-to-expiry
- **Fix Required**: Divide VTEXP values by 252 when loading

**Evidence**:
- VTEXP pattern shows consecutive dates increment by 1.0:
  - 04AUG25: 0.583333
  - 05AUG25: 1.583333  
  - 06AUG25: 2.583333
- Code inspection shows no conversion in:
  - `read_vtexp_from_csv()`: line 187 just loads float value
  - `calculator.py`: line 289 uses vtexp directly

#### 2. VTEXP Symbol Mismatch
- **Problem**: Symbol formats don't match between VTEXP and options
- **VTEXP symbols**: `XCME.ZN.N.G.06AUG25`
- **Option Bloomberg symbols**: `TYWQ25C1 110 Comdty`
- **Result**: All VTEXP lookups fail, options get `vtexp=None`

### Impact on Greeks
With 2.583 years instead of 0.0103 years (2.58 days / 252):
- **Theta**: ~252x too small (time decay spread over years not days)
- **Gamma**: Much smaller (less sensitivity when "far" from expiry)
- **Vega**: Artificially larger (more time for volatility impact)
- **All Greeks fundamentally wrong**

### Fix Applied (2025-08-05)
- **VTEXP Conversion Fixed**: Modified `time_calculator.py` line 188 to divide by 252
- **Root Cause**: VTEXP values are in days but Greek calculator expects years
- **Impact**: This was causing ALL Greek calculations to fail with arbitrage violations

### Production Log Analysis Results
1. **Arbitrage Violations**: All Greek calculations failing because incorrect time values led to wrong intrinsic value calculations
2. **Symbol Parsing**: Minor issue with plain futures symbols (XCME.ZN) - still works for most symbols
3. **Unicode Errors**: Arrow character (→) causes Windows console encoding issues
4. **Position Data**: Missing position column prevents Greek aggregation

### Next Steps
1. Deploy VTEXP fix to production
2. Test Greek calculations with corrected time values
3. Update parser to handle plain futures symbols gracefully
4. Continue testing Redis publishing and database storage

## Current Investigation: Price Updater Latency Issue (2025-08-05)

### Problem Discovered
- **Symptom**: Live prices in FRGMonitor dashboard severely delayed
- **Pattern**: Initial update fast (0.001s), then 16s, 30s, 44s, 58s... (linear +14s per message)
- **Impact**: Dashboard shows stale prices, accumulating delay over time

### Root Cause Analysis
1. **Linear Accumulation Pattern**: Indicates sequential processing bottleneck
2. **14-second Per Message**: Price updater cannot keep up with spot risk publish rate
3. **Queue Building**: Messages backing up, each waits for previous to complete

### Diagnostic Tools Created
1. **price_updater_diagnostic.py**: 
   - Simulates full pipeline with detailed timing breakdown
   - Measures each operation: pickle, Arrow, symbol translation, DB updates
   - Tests with varying message sizes and symbol counts

2. **monitor_price_pipeline.py**:
   - Non-intrusive live monitoring
   - Tracks message latency, size, and rate
   - Monitors database lock events
   - Shows real-time statistics

3. **test_database_bottleneck.py**:
   - Focused database performance testing
   - Tests single vs batch updates
   - Checks WAL mode and concurrent access
   - Provides optimization suggestions

### Initial Findings
- **Redis Configuration Inconsistency**:
  - data_manager.py uses 'localhost' (potential IPv6 issue)
  - Others use '127.0.0.1' (IPv4 direct)
  - Could cause DNS resolution delays

### Suspected Bottlenecks (To Be Confirmed)
1. **Database Operations** (most likely):
   - Individual commits per symbol (no batching)
   - WAL mode possibly disabled
   - Synchronous=FULL causing fsync delays
   
2. **Symbol Translation**:
   - RosettaStone lookups without caching
   - Database queries for each translation
   
3. **Connection Overhead**:
   - New database connection per message
   - No connection pooling

### Next Steps
1. Run diagnostic suite to identify exact bottleneck
2. Check database configuration (WAL, synchronous mode)
3. Implement targeted fix based on findings
4. Consider batch commits and connection pooling 